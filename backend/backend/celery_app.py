from pathlib import Path
from dotenv import load_dotenv
import os
from celery import Celery

# Load .env độc lập — Celery worker không qua main.py
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path if _env_path.exists() else None)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_BACKEND_URL = REDIS_URL.rsplit("/", 1)[0] + "/1"

celery_app = Celery(
    "agent",
    broker=REDIS_URL,
    backend=REDIS_BACKEND_URL,
    include=["backend.agent.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    worker_concurrency=4,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)