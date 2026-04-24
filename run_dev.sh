#!/usr/bin/env bash
# Run FastAPI service and Discord bot together for local development
set -e

export $(grep -v '^#' .env | xargs)

uv run uvicorn issue_tracker_client_service.app:app --reload &
API_PID=$!

uv run python -m issue_tracker_client_service.discord_bot &
BOT_PID=$!

cleanup() {
  kill "$API_PID" "$BOT_PID"
}

trap cleanup EXIT

wait