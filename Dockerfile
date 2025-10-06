# Scholarport Backend Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  DJANGO_ENV=production

# Create app user
RUN useradd -m -u 1000 scholarport && \
  mkdir -p /app/logs /app/staticfiles && \
  chown -R scholarport:scholarport /app

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/scholarport/.local

# Copy application code
COPY --chown=scholarport:scholarport . .

# Update PATH
ENV PATH=/home/scholarport/.local/bin:$PATH

# Switch to app user
USER scholarport

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/chat/health/')" || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Simplified config: removed --preload which was causing startup issues
# Using single worker to avoid memory issues on t2.micro
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300", "--graceful-timeout", "120", "--worker-class", "sync", "--log-level", "info", "scholarport_backend.wsgi:application"]
