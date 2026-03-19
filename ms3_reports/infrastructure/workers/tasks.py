import traceback
import gc
from infrastructure.celery_app import celery_app
from infrastructure.redis.job_metadata_store import JobMetadataStore
from application.use_cases.generate_report_use_case import GenerateReportUseCase
from celery import Task


class ReportTaskBase(Task):
    """Base Task that updates job metadata on final failure."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # args expected: payload, job_id
        try:
            job_id = None
            if args and len(args) >= 2:
                job_id = args[1]
            else:
                job_id = kwargs.get("job_id")
            if job_id:
                job_store = JobMetadataStore.from_env()
                # mark final failure
                job_store.update_status(job_id, "FAILED")
                # store the exception text if available
                try:
                    tb = traceback.format_exc()
                except Exception:
                    tb = str(exc)
                sanitized = (tb or str(exc))[-3000:]
                job_store.set_error(job_id, sanitized)
        except Exception:
            # never let on_failure raise
            pass
        return super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
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
    # mark started (idempotent)
    job_store.update_status(job_id, "STARTED")
    try:
        usecase = GenerateReportUseCase()
        usecase.run(payload, job_id)
        job_store.update_status(job_id, "SUCCESS")
    except Exception as exc:  # noqa: B902 - let autoretry handle retries
        # capture a sanitized traceback for diagnostics
        tb = traceback.format_exc()
        sanitized = tb[-3000:]
        try:
            job_store.set_error(job_id, sanitized)
        except Exception:
            pass
        # cleanup memory after failure attempt
        try:
            gc.collect()
        except Exception:
            pass
        # re-raise to trigger Celery autoretry (configured via decorator)
        raise
