from pathlib import Path
from dotenv import load_dotenv
import os
import redis.asyncio as aioredis
import redis as sync_redis

# Load .env độc lập — cần thiết khi Celery worker khởi động không qua main.py
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path if _env_path.exists() else None)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Async client — dùng trong FastAPI (SSE endpoint)
async_redis = aioredis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

# Sync client — dùng trong Celery task (sync context)
sync_redis_client = sync_redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)