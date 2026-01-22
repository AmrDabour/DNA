# ========================================
# Prediction Service - ML Predictions
# ========================================
FROM python:3.11-slim

# Labels
LABEL service="prediction-service"
LABEL version="1.0.0"
LABEL description="GenovaAI ML Prediction Microservice"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PREDICTION_SERVICE_PORT=5003
ENV MODEL_PATH=/app/models

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

# Copy ML models
# Note: shared modules are mounted at runtime via docker-compose
COPY models/ /app/models/

# Copy service code
COPY . .

# Change ownership to non-root user
RUN chown -R genovaai:genovaai /app

# Switch to non-root user
USER genovaai

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--threads", "4", "--timeout", "300", "app:app"]
