"""
Celery application configuration.
Workers process long-running tasks: parsing, matching, compilation, evaluation.
"""

from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "career_compiler",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # fair task distribution
    task_routes={
        "src.tasks.parse_resume": {"queue": "parsing"},
        "src.tasks.match_requirements": {"queue": "matching"},
        "src.tasks.compile_latex": {"queue": "compilation"},
        "src.tasks.evaluate_resume": {"queue": "evaluation"},
    },
)


# ── Task stubs (Phase 1 — actual logic runs synchronously in service layer) ───

@celery_app.task(name="src.tasks.parse_resume", bind=True, max_retries=3)
def task_parse_resume(self, resume_id: str, user_id: str):
    """
    Celery task: parse a master resume asynchronously.
    Phase 1: logic runs synchronously in the router.
    Phase 3+: this task will call run_parse_pipeline().
    """
    # TODO: Phase 3 — call parser service async from here
    return {"status": "stub", "resume_id": resume_id}
