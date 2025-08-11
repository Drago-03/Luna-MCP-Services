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

# Copy project metadata & dependency manifests early for better layer caching
COPY pyproject.toml uv.lock requirements.txt README.md /app/

# Install production dependencies (prefer uv.lock if present, fallback to requirements.txt)
RUN pip install --upgrade pip uv \
 && if [ -f uv.lock ]; then \
            echo 'Using uv.lock for deterministic install'; \
            uv sync --no-dev --frozen || { echo 'uv sync failed; falling back to pip requirements.txt'; pip install --no-cache-dir -r requirements.txt; }; \
        else \
            pip install --no-cache-dir -r requirements.txt; \
        fi

# Copy source code last (invalidate layer only when code changes)
COPY mcp-bearer-token/ mcp-bearer-token/
COPY tools/ tools/
COPY github_oauth/ github_oauth/
COPY public/ public/
COPY start.sh start.sh
RUN chmod +x start.sh

EXPOSE 8086

# Allow Render/other platforms to supply a dynamic $PORT (fallback 8086)
ENV PORT=8086
CMD ["./start.sh"]
