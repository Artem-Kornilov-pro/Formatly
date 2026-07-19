import asyncio
import uuid

from celery import Celery

from app.core.config import get_settings
from app.pipeline.run import process_job as _process_job_async

settings = get_settings()

celery_app = Celery("formatly", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="formatly.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="formatly.process_job")
def process_job(job_id: str) -> None:
    asyncio.run(_process_job_async(uuid.UUID(job_id)))
