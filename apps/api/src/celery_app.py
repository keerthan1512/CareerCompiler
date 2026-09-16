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
        "src.tasks.analyze_job": {"queue": "parsing"},
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

@celery_app.task(name="src.tasks.analyze_job", bind=True, max_retries=3)
def task_analyze_job(self, job_id: str, user_id: str):
    """
    Celery task: analyze a job description asynchronously.
    Phase 2: This task will call the job_analyzer service.
    """
    import asyncio
    from src.database import AsyncSessionLocal
    from src.models.job_description import JobDescription
    from src.models.parse_job import ParseJob
    from datetime import datetime, timezone
    
    # We must run the async job analyzer in an event loop
    async def _analyze():
        from career_compiler_job_intelligence.analyzer import JobAnalyzer
        async with AsyncSessionLocal() as session:
            job = await session.get(JobDescription, job_id)
            if not job:
                return
            
            try:
                analyzer = JobAnalyzer()
                extracted = await analyzer.analyze(job.raw_text)
                job.extracted_data = extracted.model_dump()
                job.status = "complete"
                await session.commit()
            except Exception as e:
                job.status = "failed"
                await session.commit()
                # Log error
                import logging
                logging.error(f"Failed to analyze job: {e}")

    asyncio.run(_analyze())
    return {"status": "complete", "job_id": job_id}


@celery_app.task(name="src.tasks.generate_tailoring_plan", bind=True, max_retries=3)
def task_generate_tailoring_plan(self, plan_id: str):
    """
    Background task to run the matching engine and generate a tailoring plan.
    """
    import asyncio
    from src.database import AsyncSessionLocal
    from src.models import TailoringPlan, CanonicalProfile, JobDescription
    from career_compiler_matching_engine.engine import MatchingEngine
    
    async def _generate():
        async with AsyncSessionLocal() as session:
            plan = await session.get(TailoringPlan, plan_id)
            if not plan:
                return
            
            job = await session.get(JobDescription, plan.job_id)
            
            from sqlalchemy.future import select
            res = await session.execute(select(CanonicalProfile).where(CanonicalProfile.master_resume_id == plan.master_resume_id))
            profile = res.scalar_one_or_none()
            
            if not job or not profile:
                plan.status = "failed"
                await session.commit()
                return

            try:
                engine = MatchingEngine()
                
                # We need the parsed dictionary for the canonical profile and extracted_data for JD
                result = await engine.generate_tailoring_plan(
                    canonical_profile=profile.profile_json,
                    job_description=job.extracted_data or {"raw_text": job.raw_text}
                )
                
                plan.items = [item.model_dump() for item in result.items]
                plan.status = "complete"
                plan.metadata_obj = {
                    "total_proposed": len(plan.items)
                }
                await session.commit()
            except Exception as e:
                plan.status = "failed"
                await session.commit()
                import logging
                logging.error(f"Failed to generate tailoring plan: {e}")

    asyncio.run(_generate())
    return {"status": "complete", "plan_id": plan_id}

