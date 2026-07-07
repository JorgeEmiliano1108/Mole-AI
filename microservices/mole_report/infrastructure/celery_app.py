from celery import Celery
from app.config import settings


def create_celery():
    base_url = settings.ms3_redis_url
    broker = settings.ms3_celery_broker_url or base_url
    backend = settings.ms3_celery_result_backend or base_url

    celery = Celery("ms3_reports", broker=broker, backend=backend)
    celery.conf.task_default_queue = 'reports_queue'
    celery.conf.task_acks_late = True
    celery.conf.worker_prefetch_multiplier = 1
    celery.conf.task_soft_time_limit = settings.ms3_task_soft_time_limit

    return celery


celery_app = create_celery()

try:
    import infrastructure.workers.tasks  # noqa: F401
except Exception as e:
    print(f"Error loading MS3 tasks: {e}")
