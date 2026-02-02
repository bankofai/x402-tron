#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FETCH_SCRIPT="$SCRIPT_DIR/fetch_image.ts"

URL="${1:-${IMAGE_FINDER_URL:-http://localhost:8000/protected}}"

IMAGE_FINDER_URL="$URL" npx tsx "$FETCH_SCRIPT" \
  </dev/null
