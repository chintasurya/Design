#!/usr/bin/env bash
# Build Agent_Console.zip (Metadata API format) for Workbench -> Migration -> Deploy.
# Needs the Salesforce CLI. Run set-gateway-url.sh first, or edit the URL in Setup after deploying.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
sf project convert source --source-dir "$ROOT/force-app" --output-dir "$OUT/Agent_Console" >/dev/null
rm -f "$ROOT/Agent_Console.zip"
(cd "$OUT" && zip -qr "$ROOT/Agent_Console.zip" Agent_Console)
echo "wrote $ROOT/Agent_Console.zip"
