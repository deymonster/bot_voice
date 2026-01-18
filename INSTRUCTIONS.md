# Инструкция по тестированию и запуску Voice Bot

Этот документ описывает три сценария запуска:
1. **Docker Compose (Рекомендуемый)**.
2. **Локальный тест** (в виртуальном окружении на ноутбуке).
3. **Запуск на сервере** (Production).

---

## Предварительная подготовка (Для всех вариантов)

1. **Создайте бота в Telegram:**
   - Напишите [@BotFather](https://t.me/BotFather).
   - Используйте команду `/newbot`.
   - Получите `BOT_TOKEN`.
   - В настройках бота через `/setjoingroups` разрешите добавление в группы.
   - В настройках бота через `/setprivacy` выключите Group Privacy (Disable), чтобы бот видел сообщения, или сделайте его админом в группе.

2. **Получите ID чатов:**
   - Напишите боту [@userinfobot](https://t.me/userinfobot) чтобы узнать свой ID (это будет `ADMIN_ID`).
   - Добавьте бота в нужную группу и отправьте `/start`. Используйте сторонние боты (например, `@idbot`) или логи вашего бота, чтобы узнать ID группы (обычно начинается с `-100...`).

---

## Вариант 1: Docker Compose (Рекомендуемый)
*Самый простой способ, не требует установки Python и FFmpeg локально.*

### Требования
- Docker Desktop (macOS/Windows) или Docker Engine (Linux).

### Шаги
1. **Настройте окружение:**
   Скопируйте пример и заполните токен.
   ```bash
   cp .env.example .env
   # Отредактируйте .env
   ```

2. **Запустите бота:**
   ```bash
   docker compose up -d --build
   ```
   *Параметр `-d` запускает в фоновом режиме. Уберите его, если хотите видеть логи сразу.*

3. **Смотреть логи:**
   ```bash
   docker compose logs -f
   ```

4. **Остановить бота:**
   ```bash
   docker compose down
   ```

---

## Вариант 2: Локальный тест (Virtual Environment)
*Подходит для разработки.*

### Требования
- Python 3.11+
- FFmpeg (Обязательно!)

### Установка FFmpeg (macOS)
1. **Установите FFmpeg:**
   ```bash
   brew install ffmpeg
   ```
2. **Установите pkg-config:**
   ```bash
   brew install pkg-config
   ```
3. **Экспорт переменных (Если ошибка сборки av):**
   ```bash
   export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
   # Или для Apple Silicon (M1/M2):
   # export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
   ```

### Шаги запуска
1. **Создайте и активируйте venv:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Запустите:**
   ```bash
   python -m app.bot
   ```

---

## Вариант 3: Запуск на Сервере (Production)
*Ubuntu/Debian Server.*

### Шаги
1. **Установите Docker:**
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose-plugin -y
   ```

2. **Запустите:**
   ```bash
   docker compose up -d --build
   ```

3. **Мониторинг:**
   ```bash
   docker compose logs -f
   ```

---

## Тестирование Функционала

### 1. Тест Whitelist
1. В `.env` установите `ALLOWED_CHATS=12345` (выдуманный ID).
2. Перезапустите бота (`docker compose restart`).
3. Отправьте сообщение. Бот должен **проигнорировать** его.
4. Верните свой ID.

### 2. Тест Rate Limiting
1. Отправьте 5 коротких голосовых сообщений подряд.
2. На 4-м сообщении бот должен замолчать для вас.
3. В логах: `WARNING Rate limit exceeded`.
