#!/usr/bin/env bash
# Export the deck: one 1600x900 PNG per slide + a 3-page PDF.
#   ./render.sh [outDir]      (default: ./export)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$DIR/export}"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
mkdir -p "$OUT"

NO_PROXY='127.0.0.1,localhost' node "$DIR/tools/shot.mjs" "$OUT"

"$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=6000 \
  --no-pdf-header-footer --print-to-pdf="$OUT/shieldforge-deck.pdf" \
  "file://$DIR/index.html?print=1" >/dev/null 2>&1
echo "  wrote $OUT/shieldforge-deck.pdf"
