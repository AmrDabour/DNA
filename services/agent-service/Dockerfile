# ========================================
# Agent Service - LangGraph DNA Agent
# ========================================
FROM python:3.11-slim

# Labels
LABEL service="agent-service"
LABEL version="1.0.0"
LABEL description="GenovaAI LangGraph Agent Microservice"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV AGENT_SERVICE_PORT=5005
ENV AGENT_MODEL=gemini-2.5-flash

# Create non-root user
RUN groupadd -r genovaai && useradd -r -g genovaai genovaai

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent module
COPY agent/ /app/agent/

# Copy service code
COPY . .

# Change ownership to non-root user
RUN chown -R genovaai:genovaai /app

# Switch to non-root user
USER genovaai

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "2", "--threads", "4", "--timeout", "300", "app:app"]
