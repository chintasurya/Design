#!/usr/bin/env bash
# Dump the geometry and styling of the deck's editable copy as JSON on stdout.
# The PPTX builder uses it to place native text boxes over the artwork.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHROME="${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}"

"$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --force-device-scale-factor=1 --window-size=1600,987 --virtual-time-budget=8000 \
  --user-data-dir="$(mktemp -d)" --dump-dom "file://$DIR/index.html?measure=1" 2>/dev/null \
| python3 -c '
import sys, re, html, json
dom = sys.stdin.read()
m = re.search(r"<pre id=\"__measure\">(.*?)</pre>", dom, re.S)
if not m:
    sys.exit("measure mode produced no output")
blocks = json.loads(html.unescape(m.group(1)))
if not blocks:
    sys.exit("measure mode found no editable text")
json.dump(blocks, sys.stdout, indent=1)
'
