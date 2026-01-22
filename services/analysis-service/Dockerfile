# ========================================
# Analysis Service - SNP Analysis
# ========================================
FROM python:3.11-slim

# Labels
LABEL service="analysis-service"
LABEL version="1.0.0"
LABEL description="GenovaAI Analysis Microservice"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV ANALYSIS_SERVICE_PORT=5002
ENV UPLOADS_PATH=/app/uploads

# Create non-root user
RUN groupadd -r genovaai && useradd -r -g genovaai genovaai

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
# Note: shared modules are mounted at runtime via docker-compose
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads && chown -R genovaai:genovaai /app

# Switch to non-root user
USER genovaai

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
