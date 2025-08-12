# Multi-stage Dockerfile for User Behavior Analytics Platform
# Optimized for production deployment with security and performance considerations

# ================================
# Stage 1: Base Dependencies
# ================================
FROM python:3.11-slim AS base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ================================
# Stage 2: Dependencies Installation
# ================================
FROM base AS dependencies

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with caching optimization
RUN pip install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# ================================
# Stage 3: Application Setup
# ================================
FROM base AS application

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r analytics && \
    useradd -r -g analytics -u 1000 -m -s /bin/bash analytics

# Create application directories with proper permissions
RUN mkdir -p /app/data/uploads \
             /app/data/processed \
             /app/reports \
             /app/logs \
             /app/config && \
    chown -R analytics:analytics /app

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=analytics:analytics . .

# Copy entry point and utility scripts
COPY --chown=analytics:analytics entrypoint.sh /app/entrypoint.sh
COPY --chown=analytics:analytics healthcheck.py /app/healthcheck.py
COPY --chown=analytics:analytics config_validator.py /app/config_validator.py
COPY --chown=analytics:analytics startup_monitor.py /app/startup_monitor.py
COPY --chown=analytics:analytics load_env.py /app/load_env.py

# Copy .env.example as template (actual .env should be mounted or provided via environment)
COPY --chown=analytics:analytics .env.example /app/.env.example

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/healthcheck.py /app/config_validator.py /app/startup_monitor.py /app/load_env.py

# ================================
# Stage 4: Production Image
# ================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r analytics && \
    useradd -r -g analytics -u 1000 -m -s /bin/bash analytics

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Create application directories
RUN mkdir -p /app/data/uploads \
             /app/data/processed \
             /app/reports \
             /app/logs \
             /app/config && \
    chown -R analytics:analytics /app

# Set working directory
WORKDIR /app

# Copy application code and entry point script
COPY --from=application --chown=analytics:analytics /app .

# Switch to non-root user
USER analytics

# Expose port
EXPOSE 8501

# Health check using our enhanced health check script
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD python3 /app/healthcheck.py || exit 1

# Set entry point
ENTRYPOINT ["/app/entrypoint.sh"]

# ================================
# Stage 5: Security-Hardened Production Image
# ================================
FROM production AS production-secure

# Switch back to root temporarily for security configurations
USER root

# Remove unnecessary packages and clean up
RUN apt-get update && apt-get remove -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Set up read-only root filesystem preparation
# Create necessary writable directories
RUN mkdir -p /tmp-app /var-app && \
    chown analytics:analytics /tmp-app /var-app

# Remove shell access for security (optional, can be enabled for debugging)
# RUN rm -rf /bin/bash /bin/sh /usr/bin/sh

# Set strict file permissions
RUN find /app -type f -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \; && \
    chmod +x /app/entrypoint.sh /app/healthcheck.py /app/monitoring_endpoints.py /app/container_config_manager.py

# Switch back to non-root user
USER analytics

# Security labels and metadata
LABEL security.scan="enabled" \
      security.non-root="true" \
      security.readonly-rootfs="supported" \
      security.capabilities="minimal" \
      maintainer="analytics-platform-team" \
      version="1.0.0-secure"

# Default security-focused entry point
ENTRYPOINT ["/app/entrypoint.sh"]