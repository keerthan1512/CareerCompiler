#!/usr/bin/env bash
# seed_dev_data.sh — Create a dev user record and seed test data

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$ROOT_DIR/.env" ]; then
  set -a && source "$ROOT_DIR/.env" && set +a
fi

DB_URL="${DATABASE_URL:-postgresql+asyncpg://ccuser:ccpassword@localhost:5432/careercompiler}"
# Convert to psql-compatible URL
PSQL_URL="${DB_URL/postgresql+asyncpg/postgresql}"

DEV_USER_ID="${DEV_USER_ID:-dev-user-00000000-0000-0000-0000-000000000001}"
DEV_USER_EMAIL="dev@careercompiler.local"
DEV_USER_NAME="Dev User"

echo "🌱 Seeding dev data..."

docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T postgres psql \
  -U "${POSTGRES_USER:-ccuser}" \
  -d "${POSTGRES_DB:-careercompiler}" \
  -c "
    INSERT INTO users (id, email, name, role)
    VALUES ('$DEV_USER_ID', '$DEV_USER_EMAIL', '$DEV_USER_NAME', 'individual')
    ON CONFLICT (id) DO NOTHING;
  "

echo "✅ Dev user seeded:"
echo "   ID:    $DEV_USER_ID"
echo "   Email: $DEV_USER_EMAIL"
echo ""
echo "   Use this header in API requests:"
echo "   X-Dev-User-Id: $DEV_USER_ID"
