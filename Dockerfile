# =============================================================================
# RAG Enterprise Production Dockerfile
# Multi-stage optimized build targeting <500MB final image size
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Image
# Python 3.11 slim-bookworm for minimal footprint
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime system dependencies only
# libpq5: PostgreSQL client library
# curl: Health checks
# ca-certificates: SSL/TLS support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Set working directory
WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 2: Builder
# Compile dependencies with build tools, then discard
# -----------------------------------------------------------------------------
FROM base AS builder

# Install build dependencies
# gcc, g++: Compile Python C extensions
# libpq-dev: PostgreSQL development headers
# git: For git-based dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy production requirements file (no dev dependencies)
COPY requirements-prod.txt .

# Install Python dependencies into virtual environment
# --no-cache-dir: Reduce image size
# --compile: Pre-compile bytecode for faster startup
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-prod.txt && \
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + && \
    find /opt/venv -type f -name '*.pyc' -delete && \
    find /opt/venv -type f -name '*.pyo' -delete

# -----------------------------------------------------------------------------
# Stage 3: Runtime
# Minimal production image with compiled dependencies
# -----------------------------------------------------------------------------
FROM base AS runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser agents/ /app/agents/

# Create required directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check configuration
# Checks FastAPI /health endpoint every 30s
# Waits 60s for startup before first check
# Timeout 10s per check
# 3 consecutive failures mark container unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Run FastAPI with Uvicorn
# --host 0.0.0.0: Listen on all interfaces
# --port 8000: Standard HTTP port
# --workers: Set via environment variable (default: 1)
# --timeout-keep-alive: Keep connections alive for 75s
CMD uvicorn app.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${UVICORN_WORKERS:-1} \
    --timeout-keep-alive 75 \
    --log-level info

# -----------------------------------------------------------------------------
# Image Optimization Summary
# -----------------------------------------------------------------------------
# - Multi-stage build separates build tools from runtime
# - Virtual environment isolation
# - Non-root user (appuser, UID 1000)
# - Minimal base image (python:3.11-slim-bookworm)
# - Removed build artifacts (__pycache__, *.pyc, *.pyo)
# - No development dependencies
# - Health check for orchestration
# - Expected size: <500MB
# -----------------------------------------------------------------------------
