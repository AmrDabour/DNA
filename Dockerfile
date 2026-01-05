# ============================================================
# DNA Genetic Prediction Web Application - Dockerfile
# Multi-stage build for optimized image size
# ============================================================

FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-warn-script-location -r requirements.txt

# ============================================================
# Production Stage
# ============================================================
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="DNA Prediction Team" \
    version="1.0.0" \
    description="DNA Genetic Prediction Web Application"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app.py .
COPY alembic.ini .
COPY models/ ./models/
COPY routes/ ./routes/
COPY services/ ./services/
COPY database/ ./database/
COPY config/ ./config/
COPY agent/ ./agent/
COPY utils/ ./utils/
COPY templates/ ./templates/
COPY static/ ./static/
COPY new_model/ ./new_model/

# Create necessary directories
RUN mkdir -p uploads instance result plots visualizations hapmap_data patient_snp_data

# Create non-root user for security (optional, comment out if causing issues)
# RUN useradd --create-home --shell /bin/bash appuser \
#     && chown -R appuser:appuser /app
# USER appuser

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# Run the application with gunicorn for production
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "app:app"]

