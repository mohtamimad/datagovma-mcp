# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.10.9 AS uv

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY --from=uv /uv /usr/local/bin/uv

# Install locked runtime dependencies first for better layer caching.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable

# Then install the project itself from source (still lockfile-driven).
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

EXPOSE 8000

USER app

ENTRYPOINT ["datagovma-mcp"]
