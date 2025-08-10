FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# System deps for Pillow (image ops) and git for cloning
RUN apt-get update \
 && apt-get install -y --no-install-recommends git libjpeg-dev zlib1g-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for layer caching
COPY pyproject.toml README.md /app/

# Install uv (fast dep manager) and sync deps (prod only)
RUN pip install --upgrade pip uv \
 && uv sync --no-dev

# Copy source
COPY mcp-bearer-token/ mcp-bearer-token/
COPY tools/ tools/
COPY github_oauth/ github_oauth/
COPY public/ public/

EXPOSE 8086

CMD ["uvicorn", "mcp-bearer-token.luna_mcp:app", "--host", "0.0.0.0", "--port", "8086"]
