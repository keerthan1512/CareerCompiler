#!/usr/bin/env bash
# run_local_stack.sh — Start the local dev infrastructure and run migrations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 CareerCompiler — Starting local dev stack"
echo "============================================"

# ── 1. Check prerequisites ─────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required. Install Docker Desktop."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.12+ is required."; exit 1; }

echo "✅ Prerequisites OK"

# ── 2. Load .env ──────────────────────────────────────────────────────────
if [ -f "$ROOT_DIR/.env" ]; then
  set -a && source "$ROOT_DIR/.env" && set +a
  echo "✅ .env loaded"
else
  echo "⚠️  .env not found — copying from .env.example"
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "   Edit $ROOT_DIR/.env with your GROQ_API_KEY and then re-run this script."
  set -a && source "$ROOT_DIR/.env" && set +a
fi

# ── 3. Start Docker services ───────────────────────────────────────────────
echo ""
echo "🐳 Starting Docker services (Postgres + Redis)..."
cd "$ROOT_DIR"
docker compose up -d postgres redis

echo "⏳ Waiting for Postgres to be healthy..."
until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-ccuser}" -d "${POSTGRES_DB:-careercompiler}" >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Postgres is healthy"

echo "⏳ Waiting for Redis..."
until docker compose exec -T redis redis-cli ping >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Redis is healthy"

# ── 4. Run Alembic migrations ─────────────────────────────────────────────
echo ""
echo "🗄️  Running database migrations..."
cd "$ROOT_DIR/apps/api"

# Activate venv if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Export DATABASE_URL for Alembic
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://ccuser:ccpassword@localhost:5432/careercompiler}"
alembic upgrade head
echo "✅ Migrations complete"

# ── 5. Create upload directory ────────────────────────────────────────────
mkdir -p "$ROOT_DIR/uploads"
echo "✅ Upload directory ready: $ROOT_DIR/uploads"

# ── 6. Done ──────────────────────────────────────────────────────────────
echo ""
echo "🎉 Local stack is ready!"
echo ""
echo "  Next steps:"
echo "  1. Start API:    cd apps/api && uvicorn src.main:app --reload"
echo "  2. Start worker: cd apps/api && celery -A src.celery_app worker --loglevel=info"
echo "  3. Start web:    cd apps/web && pnpm dev"
echo ""
echo "  API docs: http://localhost:8000/docs"
echo "  Web app:  http://localhost:3000"
