# MCP Server Dockerfile
# Multi-stage build for production deployment

# ==================== Builder Stage ====================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies only (no source code yet)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# ==================== Production Stage ====================
FROM python:3.13-slim AS production

# Security: Run as non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser -d /app -s /sbin/nologin mcpuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/app ./app
COPY config/mcp ./config/mcp

# Create required directories
RUN mkdir -p /app/logs /app/uploads /app/data \
    && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8100 \
    MCP_CONFIG_PATH=/app/config/mcp/mcp.json

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

CMD ["uvicorn", "app.mcp.server.main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "4"]
