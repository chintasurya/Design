#!/usr/bin/env bash
# Point the Agent_Gateway Named Credential at your Cloud Run URL before deploying.
#   ./scripts/set-gateway-url.sh https://agent-gateway-xxxxx-uc.a.run.app
set -euo pipefail
URL="${1:?usage: set-gateway-url.sh https://<service>.run.app}"
case "$URL" in https://*) ;; *) echo "URL must start with https://" >&2; exit 1;; esac
URL="${URL%/}"
FILE="$(cd "$(dirname "$0")/.." && pwd)/force-app/main/default/namedCredentials/Agent_Gateway.namedCredential-meta.xml"
python3 - "$FILE" "$URL" <<'PY'
import re, sys
path, url = sys.argv[1], sys.argv[2]
text = open(path).read()
new = re.sub(r"(<parameterName>Url</parameterName>\s*<parameterType>Url</parameterType>\s*<parameterValue>)[^<]*(</parameterValue>)",
             lambda m: m.group(1) + url + m.group(2), text)
assert new != text or url in text, "Url parameter not found"
open(path, "w").write(new)
print("Agent_Gateway ->", url)
PY
