import traceback
import gc
from infrastructure.celery_app import celery_app
from infrastructure.redis.job_metadata_store import JobMetadataStore
from application.use_cases.generate_report_use_case import GenerateReportUseCase
from celery import Task

class ReportTaskBase(Task):
    """Base Task that updates job metadata on final failure."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        try:
            job_id = None
            if args and len(args) >= 2:
                job_id = args[1]
            else:
                job_id = kwargs.get("job_id")
            if job_id:
                job_store = JobMetadataStore.from_env()
                job_store.update_status(job_id, "FAILED")
                try:
                    tb = traceback.format_exc()
                except Exception:
                    tb = str(exc)
                sanitized = (tb or str(exc))[-3000:]
                job_store.set_error(job_id, sanitized)
        except Exception:
            pass
        return super().on_failure(exc, task_id, args, kwargs, einfo)

# FIX: Nombre de tarea explícito para el registro exacto en el Broker

@celery_app.task(name='send_reminder', bind=True, max_retries=2)
def send_reminder(self, recipient_id: str, message: str):
    """Send a reminder (e.g., via WhatsApp) to the given recipient.
    In production this would call an external messaging service.
    In tests it will be mocked via `send_reminder.delay`.
    """
    # Placeholder implementation – real integration goes here.
    # For now we just log the intent.
    import structlog
    logger = structlog.get_logger()
    logger.info('reminder_sent', recipient_id=recipient_id, message=message)
    return True
@celery_app.task(
    name="generate_report_task",
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    retry_jitter=True,
    base=ReportTaskBase,
)
def generate_report_task(self, payload: dict, job_id: str):
    job_store = JobMetadataStore.from_env()
    job_store.update_status(job_id, "STARTED")
    try:
        usecase = GenerateReportUseCase()
        usecase.run(payload, job_id)
        job_store.update_status(job_id, "SUCCESS")
    except Exception as exc:  # noqa: B902
        tb = traceback.format_exc()
        sanitized = tb[-3000:]
        try:
            job_store.set_error(job_id, sanitized)
        except Exception:
            pass
        try:
            gc.collect()
        except Exception:
            pass
        raise