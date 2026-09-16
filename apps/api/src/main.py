"""
CareerCompiler API — FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import master_resumes, jobs, job_descriptions

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("CareerCompiler API starting up [%s]", settings.environment)

    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory: %s", settings.upload_path.resolve())

    # Test LLM connectivity (non-blocking warning only)
    if settings.groq_api_key:
        try:
            from groq_client import get_llm_client
            client = get_llm_client()
            health = client.health_check()
            logger.info("Groq LLM connectivity: %s", health["status"])
        except Exception as exc:
            logger.warning("Groq connectivity check failed: %s", exc)
    else:
        logger.warning("GROQ_API_KEY not set — LLM features disabled")

    yield

    logger.info("CareerCompiler API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────


app = FastAPI(
    title="CareerCompiler API",
    description=(
        "AI-Powered, Evidence-Grounded Resume Engineering and ATS Evaluation Platform. "
        "Upload a master LaTeX resume and generate factually grounded, job-specific variants."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(master_resumes.router, prefix=API_PREFIX)
app.include_router(job_descriptions.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Liveness probe. Returns 200 if the API is up."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "CareerCompiler API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
