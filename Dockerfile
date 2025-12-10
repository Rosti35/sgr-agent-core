# Backend Dockerfile for Railway deployment
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    uv sync --frozen --no-dev --no-install-project

# Copy the application code
COPY sgr_deep_research ./sgr_deep_research
COPY config.yaml.example ./config.yaml.example
COPY agents.yaml.example ./agents.yaml.example
COPY logging_config.yaml ./logging_config.yaml
COPY scripts ./scripts

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python -e .

FROM python:3.13-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd --gid 1000 appgroup && \
    useradd --no-create-home --shell /bin/false --uid 1000 --gid 1000 --system appuser

COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appgroup /app /app

WORKDIR /app

# Create necessary directories and make entrypoint executable
RUN mkdir -p logs reports && \
    chown -R appuser:appgroup logs reports && \
    chmod +x /app/scripts/entrypoint.sh

USER appuser:appgroup

# Railway uses PORT environment variable
ENV PORT=8010
EXPOSE ${PORT}

# Start the FastAPI server via entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

