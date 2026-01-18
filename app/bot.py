import os
import asyncio
import logging
import sys
import time
from collections import defaultdict, deque
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import CommandStart
from loguru import logger

from app.config import Config
from app.transcriber import AudioTranscriber

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Initialize bot and dispatcher
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()

# Global transcriber instance
transcriber: AudioTranscriber = None

# Rate Limiting
# Stores timestamps of requests: {user_id: deque([timestamp1, timestamp2, ...])}
user_requests = defaultdict(lambda: deque(maxlen=Config.RATE_LIMIT_REQUESTS))

def is_rate_limited(user_id: int) -> bool:
    """
    Checks if a user has exceeded the rate limit.
    Returns True if limited (should block), False otherwise.
    """
    now = time.time()
    timestamps = user_requests[user_id]
    
    # Remove old timestamps outside the window
    while timestamps and now - timestamps[0] > Config.RATE_LIMIT_WINDOW:
        timestamps.popleft()
        
    if len(timestamps) >= Config.RATE_LIMIT_REQUESTS:
        return True
        
    timestamps.append(now)
    return False

def is_chat_allowed(chat_id: int) -> bool:
    """
    Checks if the chat is in the whitelist.
    If whitelist is empty, allows all chats.
    """
    if not Config.ALLOWED_CHATS:
        return True
    return chat_id in Config.ALLOWED_CHATS

async def send_error_notification(error: Exception, context: str):
    """
    Sends error details to the admin.
    """
    if Config.ADMIN_ID:
        try:
            await bot.send_message(
                Config.ADMIN_ID, 
                f"🚨 <b>Bot Error</b>\nContext: {context}\nError: {str(error)}"
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

def split_text(text: str, limit: int = 4000) -> list[str]:
    """
    Splits long text into chunks to fit Telegram's message limit.
    """
    if len(text) <= limit:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
            
        # Find the last space within the limit to split cleanly
        split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
            
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
        
    return chunks

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    # Helpful log to find Group ID
    logger.info(f"👋 Received /start from Chat ID: {message.chat.id} | Type: {message.chat.type} | User: {message.from_user.full_name}")

    if not is_chat_allowed(message.chat.id):
        logger.warning(f"🚫 Chat {message.chat.id} is not in ALLOWED_CHATS")
        return

    await message.answer(
        f"Привет! Я бот для распознавания голосовых сообщений.\n"
        f"ID этого чата: <code>{message.chat.id}</code>\n"
        f"(Добавь этот ID в .env если хочешь ограничить доступ)",
        parse_mode="HTML"
    )

@dp.message(F.content_type == ContentType.VOICE)
async def handle_voice(message: types.Message):
    """
    Handles voice messages only.
    """
    # 0. Whitelist Check
    if not is_chat_allowed(message.chat.id):
        # Silent ignore for unauthorized chats
        return

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # 1. Rate Limiting Check
    if is_rate_limited(user_id):
        logger.warning(f"Rate limit exceeded for {user_name} ({user_id})")
        return

    logger.info(f"Received audio from {user_name}")

    # Determine file ID and type
    file_id = message.voice.file_id
    file_unique_id = message.voice.file_unique_id
    duration = message.voice.duration
    extension = "ogg"

    # 2. Skip long files (Protection from heavy files)
    if duration > 300: # 5 minutes limit
        await message.reply("⚠️ Сообщение слишком длинное для обработки (макс. 5 минут).")
        return

    # Notify user that processing started
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{file_unique_id}.{extension}"

    try:
        pending = await message.reply(f"⏳ От <b>{user_name}</b>: идёт распознавание...", parse_mode="HTML")

        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, file_path)

        text = await transcriber.transcribe(file_path)

        if not text:
            text = "[Не удалось распознать речь или тишина]"

        chunks = split_text(text)

        edited_first = False
        if chunks:
            header = f"От <b>{user_name}</b>: "
            try:
                await pending.edit_text(f"{header}{chunks[0]}", parse_mode="HTML")
                edited_first = True
            except Exception:
                edited_first = False

        start_index = 1 if edited_first else 0
        for i in range(start_index, len(chunks)):
            await message.reply(f"{header}{chunks[i]}", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error processing message from {user_name}: {e}")
        await send_error_notification(e, f"Processing message from {user_name}")
        try:
            await pending.edit_text("❌ Ошибка обработки.")
        except Exception:
            await message.reply("❌ Ошибка обработки.")
    finally:
        # Cleanup file
        if os.path.exists(file_path):
            os.remove(file_path)

# Graceful Shutdown Hook
@dp.shutdown()
async def on_shutdown():
    logger.info("Stopping bot...")
    if transcriber:
        transcriber.shutdown()
    logger.info("Bot stopped gracefully.")

async def main():
    global transcriber
    logger.info("Initializing Transcriber Model...")
    transcriber = AudioTranscriber()
    
    logger.info("Starting Bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # The shutdown hook in dp will handle cleanup
        pass
