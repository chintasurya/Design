#!/usr/bin/env bash
# Export the deck: slide PNGs, two PowerPoint files and a PDF.
#   ./render.sh [outDir]      (default: ./export)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$DIR/export}"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"
export CHROME
mkdir -p "$OUT"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
shot() { NO_PROXY='127.0.0.1,localhost' node "$DIR/tools/shot.mjs" "$@"; }

# 1. One PNG per slide, at the deck's native 1600x900.
shot "$OUT"

# 2. PowerPoint gets 2x renders (3200x1800) so slides stay crisp projected.
mkdir -p "$WORK/hi" "$WORK/bg"
shot "$WORK/hi" 2 >/dev/null
python3 "$DIR/tools/build_pptx.py" "$WORK/hi" "$OUT/shieldforge-deck.pptx"

# 3. The editable deck: the same artwork with the copy hidden, plus native
#    text boxes placed from the browser's own measurements.
shot "$WORK/bg" 2 "&bg=1" >/dev/null
"$DIR/tools/measure.sh" > "$WORK/measure.json"
python3 "$DIR/tools/build_pptx.py" "$WORK/bg" \
  "$OUT/shieldforge-deck-editable.pptx" --text "$WORK/measure.json"

# 4. PDF straight from the HTML.
"$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=6000 \
  --no-pdf-header-footer --print-to-pdf="$OUT/shieldforge-deck.pdf" \
  "file://$DIR/index.html?print=1" >/dev/null 2>&1
echo "  wrote $OUT/shieldforge-deck.pdf"
