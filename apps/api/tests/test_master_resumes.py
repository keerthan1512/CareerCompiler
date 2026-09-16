"""
API integration tests for master-resumes endpoints.
Requires Postgres and Redis running (via docker-compose).
Run: cd apps/api && python -m pytest tests/ -v
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.main import app
from src.database import Base, get_db
from src.config import get_settings

settings = get_settings()

# Use a test database URL (SQLite async for unit tests, Postgres for integration)
TEST_DB_URL = "sqlite+aiosqlite:///./test_career_compiler.db"

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "services" / "resume-parser" / "tests" / "fixtures"
SAMPLE_TEX = FIXTURE_DIR / "sample_moderncv.tex"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """HTTP client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Dev-User-Id": "11111111-1111-1111-1111-111111111111"},
    ) as c:
        yield c


# ── Health check ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "CareerCompiler" in response.json()["name"]


# ── Master Resume Upload ───────────────────────────────────────────────────────


@pytest.mark.anyio
@pytest.mark.skipif(not SAMPLE_TEX.exists(), reason="Sample fixture not found")
async def test_upload_master_resume(client):
    """Test uploading a real .tex file."""
    tex_content = SAMPLE_TEX.read_bytes()
    response = await client.post(
        "/api/v1/master-resumes",
        files={"tex_file": ("sample_moderncv.tex", tex_content, "text/plain")},
        data={"display_name": "Test Resume"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["status"] in ("complete", "failed", "pending")
    return data["id"]


@pytest.mark.anyio
async def test_upload_requires_tex_file(client):
    """Must reject non-.tex files."""
    response = await client.post(
        "/api/v1/master-resumes",
        files={"tex_file": ("resume.pdf", b"not a tex file", "application/pdf")},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_upload_rejects_empty_file(client):
    """Must reject empty files."""
    response = await client.post(
        "/api/v1/master-resumes",
        files={"tex_file": ("resume.tex", b"", "text/plain")},
    )
    assert response.status_code == 400


# ── Dev Auth ──────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_dev_auth_auto_creates_user(client):
    """Dev auth bypass should auto-create a user record."""
    response = await client.get("/api/v1/master-resumes")
    assert response.status_code == 200  # not 401


@pytest.mark.anyio
async def test_invalid_dev_user_id_rejected():
    """Invalid UUIDs in X-Dev-User-Id should return 400."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Dev-User-Id": "not-a-uuid"},
    ) as c:
        response = await c.get("/api/v1/master-resumes")
        assert response.status_code == 400
