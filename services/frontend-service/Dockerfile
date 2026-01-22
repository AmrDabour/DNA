# ========================================
# Frontend Service - Web UI & API Gateway
# ========================================
FROM python:3.11-slim

# Labels
LABEL service="frontend-service"
LABEL version="1.0.0"
LABEL description="GenovaAI Frontend & API Gateway Microservice"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FRONTEND_PORT=8080

# Create non-root user
RUN groupadd -r genovaai && useradd -r -g genovaai genovaai

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy templates and static files
# Note: shared modules are mounted at runtime via docker-compose
COPY templates/ /app/templates/
COPY static/ /app/static/

# Copy service code
COPY . .

# Change ownership to non-root user
RUN chown -R genovaai:genovaai /app

# Switch to non-root user
USER genovaai

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]
