# Agent gateway: FastAPI + Codex CLI + Salesforce CLI in one image.
# Node is the base because both CLIs ship on npm; Python runs the gateway.
FROM node:22-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Versions verified for this POC; bump deliberately, not by accident.
RUN npm install -g @openai/codex@0.163.0 @salesforce/cli@2.154.4 \
 && npm cache clean --force

WORKDIR /srv/app
COPY requirements.txt .
RUN python3 -m venv /srv/venv && /srv/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN useradd --create-home --uid 10001 agent \
 && mkdir -p /srv/codex-home /tmp/agent-runs \
 && chown -R agent /srv/codex-home /tmp/agent-runs
USER agent

ENV PATH="/srv/venv/bin:$PATH" \
    CODEX_HOME_DIR=/srv/codex-home \
    WORKSPACE_ROOT=/tmp/agent-runs \
    PYTHONUNBUFFERED=1 \
    PORT=8080

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
