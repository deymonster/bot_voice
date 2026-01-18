import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MODEL_SIZE = os.getenv("MODEL_SIZE", "medium")  # tiny, base, small, medium, large-v3
    DEVICE = os.getenv("DEVICE", "cpu")  # cpu or cuda
    COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")  # int8, float16, float32
    
    # Performance & Limits
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "1"))  # How many transcriptions run in parallel
    
    # Rate Limiting (Anti-flood)
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "3"))  # Max requests per user
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))     # Time window in seconds
    
    # Security & Monitoring
    # Split by comma and filter empty strings
    ALLOWED_CHATS = [int(x.strip()) for x in os.getenv("ALLOWED_CHATS", "").split(",") if x.strip()]
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

    # Performance tuning for CPU
    CPU_THREADS = int(os.getenv("CPU_THREADS", "0"))  # 0 = auto (use all cores)
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", "1"))  # internal workers in faster-whisper
    INITIAL_PROMPT = os.getenv("INITIAL_PROMPT", "")  # prompt to bias transcription
    LOCAL_FILES_ONLY = os.getenv("LOCAL_FILES_ONLY", "false").lower() == "true"

    # Decoding parameters
    BEAM_SIZE = int(os.getenv("BEAM_SIZE", "2"))
    WITHOUT_TIMESTAMPS = os.getenv("WITHOUT_TIMESTAMPS", "true").lower() == "true"
    CONDITION_ON_PREVIOUS_TEXT = os.getenv("CONDITION_ON_PREVIOUS_TEXT", "false").lower() == "true"
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables")
