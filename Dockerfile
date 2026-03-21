# Stage 1: Build — install dependencies with uv
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace root config and lockfile first (better layer caching)
COPY pyproject.toml uv.lock ./

# Copy all workspace members (uv needs full workspace context to resolve)
COPY components/ components/

# Install production dependencies only
RUN uv sync --all-packages --no-dev --frozen

# Stage 2: Runtime — slim image without build tools
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8000

# Render sets PORT env var; default to 8000 for local development
CMD ["sh", "-c", "uv run uvicorn issue_tracker_client_service.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
