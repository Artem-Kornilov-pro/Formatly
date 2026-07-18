from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("formatly", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="formatly.ping")
def ping() -> str:
    return "pong"
