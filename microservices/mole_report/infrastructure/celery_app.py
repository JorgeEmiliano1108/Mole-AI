import os
from celery import Celery
from app.config import settings

def create_celery():
    # FIX: Manejo seguro de la URL de Redis (evita concatenaciones inválidas como /2/1)
    # Por defecto apuntamos a la base de datos 2 para no chocar con Django
    base_redis_url = os.getenv("REDIS_URL", "redis://redis:6379/2")
    
    broker = os.getenv("MS3_CELERY_BROKER_URL", base_redis_url)
    backend = os.getenv("MS3_CELERY_RESULT_BACKEND", base_redis_url)
    
    celery = Celery("ms3_reports", broker=broker, backend=backend)
    
    # FIX: AISLAMIENTO ESTRICTO DE COLAS
    # Garantiza que MS3 solo produzca y consuma tareas en su carril exclusivo
    celery.conf.task_default_queue = 'reports_queue'
    
    # Optimizaciones para tareas pesadas (PDFs / ML)
    celery.conf.task_acks_late = True
    celery.conf.worker_prefetch_multiplier = 1
    celery.conf.task_soft_time_limit = int(os.getenv("MS3_TASK_SOFT_TIME_LIMIT", "600"))
    
    return celery

celery_app = create_celery()

# Ensure tasks are imported so they register with the Celery app
try:
    import infrastructure.workers.tasks  # noqa: F401
except Exception as e:
    print(f"Error loading MS3 tasks: {e}")