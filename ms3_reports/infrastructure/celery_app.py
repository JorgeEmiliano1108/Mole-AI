import os
from celery import Celery
from app.config import settings


def create_celery():
    broker = os.getenv("MS3_CELERY_BROKER_URL", settings.REDIS_URL + "/1")
    backend = os.getenv("MS3_CELERY_RESULT_BACKEND", settings.REDIS_URL + "/2")
    celery = Celery("ms3_reports", broker=broker, backend=backend)
    celery.conf.task_acks_late = True
    celery.conf.worker_prefetch_multiplier = 1
    celery.conf.task_soft_time_limit = int(os.getenv("MS3_TASK_SOFT_TIME_LIMIT", "600"))
    return celery


celery_app = create_celery()
# Ensure tasks are imported so they register with the Celery app
try:
    import infrastructure.workers.tasks  # noqa: F401
except Exception:
    pass
