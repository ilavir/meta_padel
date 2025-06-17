FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
       curl \
       gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy the content of the local directory to the working directory
COPY app/ app/
COPY migrations/ migrations/
COPY tennis.py config.py logging.conf start.sh init_db.py ./

# Set correct permissions
RUN chown -R appuser:appuser /app \
    && chmod +x start.sh

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 5100

# Run the application with production server
ENTRYPOINT ["./start.sh"]