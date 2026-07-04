from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "tarot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-subscription-expiry": {
            "task": "app.infrastructure.tasks.check_subscription_notifications",
            "schedule": crontab(hour=9, minute=0),
        },
        "check-inactive-users": {
            "task": "app.infrastructure.tasks.check_inactive_users",
            "schedule": crontab(hour=10, minute=0),
        },
        "send-daily-card-push": {
            "task": "app.infrastructure.tasks.send_daily_card_push",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.infrastructure"])
