# Multi-stage Dockerfile for Factory ERP System
# Optimized for production deployment with security and performance

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt requirements-core.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG APP_VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

# Add metadata labels
LABEL maintainer="Factory ERP Team" \
      version="${APP_VERSION}" \
      description="Factory ERP Data Management System" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r factory && useradd -r -g factory factory

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY run_tests.py ./

# Create necessary directories and set permissions
RUN mkdir -p logs uploads static && \
    chown -R factory:factory /app && \
    chmod -R 755 /app

# Copy startup scripts
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/start-server.sh /start-server.sh
COPY docker/healthcheck.py /healthcheck.py

# Make scripts executable
RUN chmod +x /entrypoint.sh /start-server.sh && \
    chown factory:factory /entrypoint.sh /start-server.sh /healthcheck.py

# Switch to non-root user
USER factory

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /healthcheck.py || exit 1

# Set environment variables
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODULE="app.main:app" \
    HOST="0.0.0.0" \
    PORT="8000" \
    WORKERS="4" \
    WORKER_CLASS="uvicorn.workers.UvicornWorker" \
    LOG_LEVEL="info" \
    KEEP_ALIVE="2"

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["/start-server.sh"]