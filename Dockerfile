# Multi-stage build for production optimization
FROM python:3.13-slim AS builder

# Set environment variables for build stage
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
    /opt/venv/bin/pip install gunicorn

# Production stage
FROM python:3.13-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_ENV=production

# Install runtime dependencies and security updates
RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
       curl \
       ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
RUN chown -R appuser:appuser /opt/venv

# Copy application files with proper ownership
COPY --chown=appuser:appuser app/ app/
COPY --chown=appuser:appuser migrations/ migrations/
COPY --chown=appuser:appuser tennis.py config.py logging.conf start.sh init_app.py ./

# Create required directories with proper permissions
RUN mkdir -p app/static/uploads/avatars \
    && chown -R appuser:appuser /app \
    && chmod +x start.sh \
    && chmod +x init_app.py

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 5100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5100/health || exit 1

# Use exec form for better signal handling
ENTRYPOINT ["./start.sh"]