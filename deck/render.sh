#!/usr/bin/env bash
# Export the deck: one 1600x900 PNG per slide, a 3-page PDF, and a PPTX.
#   ./render.sh [outDir]      (default: ./export)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$DIR/export}"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
mkdir -p "$OUT"

NO_PROXY='127.0.0.1,localhost' node "$DIR/tools/shot.mjs" "$OUT"

# PowerPoint gets its own 2x renders (3200x1800) so slides stay crisp projected.
HIRES="$(mktemp -d)"
trap 'rm -rf "$HIRES"' EXIT
NO_PROXY='127.0.0.1,localhost' node "$DIR/tools/shot.mjs" "$HIRES" 2 >/dev/null
python3 "$DIR/tools/build_pptx.py" "$HIRES" "$OUT/shieldforge-deck.pptx"

"$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=6000 \
  --no-pdf-header-footer --print-to-pdf="$OUT/shieldforge-deck.pdf" \
  "file://$DIR/index.html?print=1" >/dev/null 2>&1
echo "  wrote $OUT/shieldforge-deck.pdf"
