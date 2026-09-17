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
def task_parse_resume(self, resume_id: str, user_id: str, filename: str):
    """
    Celery task: parse a master resume asynchronously using PdfParser.
    """
    import asyncio
    
    async def _parse():
        from src.config import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        engine = create_async_engine(get_settings().database_url)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        from src.models import MasterResume, CanonicalProfile
        from src.services.file_storage import get_file_storage
        from career_compiler_resume_parser.parser import PdfParser
        import logging
        
        await engine.dispose()
        
        async with AsyncSessionLocal() as session:
            resume = await session.get(MasterResume, resume_id)
            if not resume:
                return
            
            from sqlalchemy.future import select
            res = await session.execute(select(CanonicalProfile).where(CanonicalProfile.master_resume_id == resume_id))
            profile = res.scalar_one_or_none()
            if not profile:
                return
                
            try:
                storage = get_file_storage()
                pdf_bytes = await storage.read_pdf(user_id, resume_id, filename)
                
                parser = PdfParser()
                parsed_json = await parser.parse(pdf_bytes, filename)
                
                profile.profile_json = parsed_json
                resume.template_metadata = parsed_json.get("template", {})
                profile.status = "complete"
                await session.commit()
            except Exception as e:
                profile.status = "failed"
                profile.error_message = str(e)
                await session.commit()
                logging.error(f"Failed to parse PDF resume: {e}")

    asyncio.run(_parse())
    return {"status": "complete", "resume_id": resume_id}

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
        from src.config import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        engine = create_async_engine(get_settings().database_url)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await engine.dispose()
        
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
        from src.config import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        engine = create_async_engine(get_settings().database_url)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await engine.dispose()
        
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


@celery_app.task(name="src.tasks.compile_latex", bind=True, max_retries=3)
def task_compile_latex(self, document_id: str):
    """
    Background task to inject tailoring changes and compile LaTeX to PDF.
    """
    import asyncio
    import logging
    from src.database import AsyncSessionLocal
    from src.models import CompiledResume, TailoringPlan, MasterResume
    
    logger = logging.getLogger(__name__)
    from career_compiler_document_engineering.templater import apply_tailoring_plan
    from career_compiler_document_engineering.compiler import HtmlToPdfCompiler
    from career_compiler_document_engineering.validator import DocumentValidator
    from src.config import get_settings
    
    settings = get_settings()
    
    async def _compile():
        from src.config import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        engine = create_async_engine(get_settings().database_url)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await engine.dispose()
        
        async with AsyncSessionLocal() as session:
            doc = await session.get(CompiledResume, document_id)
            if not doc:
                return
                
            plan = await session.get(TailoringPlan, doc.tailoring_plan_id)
            if not plan:
                doc.status = "failed"
                await session.commit()
                return
                
            master = await session.get(MasterResume, plan.master_resume_id)
            if not master:
                doc.status = "failed"
                await session.commit()
                return
                
            try:
                # 1. Templater
                doc.status = "running"
                await session.commit()
                
                # Fetch CanonicalProfile JSON instead of raw tex
                from src.models import CanonicalProfile
                from sqlalchemy.future import select
                
                stmt = select(CanonicalProfile).where(CanonicalProfile.master_resume_id == master.id)
                res = await session.execute(stmt)
                profile = res.scalar_one_or_none()
                
                if not profile or not profile.profile_json:
                    raise Exception("Master resume canonical profile not found or empty.")
                
                # Apply changes to JSON
                modified_json = apply_tailoring_plan(profile.profile_json, plan.items or [])
                
                # Render HTML
                from career_compiler_document_engineering.templater import render_html
                new_html = render_html(modified_json)
                doc.latex_content = new_html # Reuse this field for HTML for now
                
                # 2. Compiler
                compiler = HtmlToPdfCompiler(upload_dir=settings.upload_dir)
                comp_result = compiler.compile(new_html)
                
                # 3. Validator
                val = DocumentValidator()
                log_path = comp_result.get("log_path")
                validation_res = {}
                if log_path:
                    with open(log_path, "r", encoding="utf-8") as f:
                        log_content = f.read()
                        validation_res = val.validate(log_content)
                
                doc.validation_results = validation_res
                
                if comp_result["status"] == "success":
                    doc.status = "complete"
                    doc.pdf_file_path = comp_result["pdf_path"]
                else:
                    doc.status = "failed"
                    # Include error in validation results
                    doc.validation_results["compilation_error"] = comp_result.get("error")
                    
                await session.commit()
                
            except Exception as e:
                logger.exception(f"Failed to compile LaTeX for doc {document_id}")
                doc.status = "failed"
                await session.commit()

    asyncio.run(_compile())
    return {"status": "complete", "document_id": document_id}
