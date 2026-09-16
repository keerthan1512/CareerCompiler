#!/usr/bin/env bash
# generate_openapi.sh — Export OpenAPI spec from running FastAPI server

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

API_URL="${API_URL:-http://localhost:8000}"
OUTPUT="$ROOT_DIR/docs/api-spec.yaml"

echo "📄 Fetching OpenAPI spec from $API_URL/openapi.json..."

# Fetch JSON spec and convert to YAML
curl -sf "$API_URL/openapi.json" | python3 -c "
import sys, json, yaml
data = json.load(sys.stdin)
print(yaml.dump(data, default_flow_style=False, allow_unicode=True))
" > "$OUTPUT"

echo "✅ OpenAPI spec written to $OUTPUT"
