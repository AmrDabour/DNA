#!/bin/bash
# ============================================================
# GenovaAI - Generate Kubernetes Secrets from .env file
# ============================================================
# Usage: ./scripts/generate-k8s-secrets.sh
# This script reads from .env and creates secrets.local.yaml
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
OUTPUT_FILE="$PROJECT_ROOT/kubernetes-manifests/secrets.local.yaml"

echo "🔐 GenovaAI - Kubernetes Secrets Generator"
echo "=========================================="

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at: $ENV_FILE"
    echo ""
    echo "Please create .env file with at least:"
    echo "  GEMINI_API_KEY=your_api_key_here"
    echo ""
    echo "Get your API key from: https://aistudio.google.com/apikey"
    exit 1
fi

# Load .env file
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Set defaults
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-local-dev-secret-key-$RANDOM}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-local-postgres-pwd}"
MONGO_PASSWORD="${MONGO_PASSWORD:-local-mongo-pwd}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD:-local-rabbitmq-pwd}"
LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-}"

# Validate required
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY is missing in .env"
    echo ""
    echo "Add this line to your .env file:"
    echo "  GEMINI_API_KEY=your_api_key_here"
    echo ""
    echo "Get your API key from: https://aistudio.google.com/apikey"
    exit 1
fi

echo "✅ Found GEMINI_API_KEY"

# Generate secrets.local.yaml
cat > "$OUTPUT_FILE" << EOF
# ============================================================
# GenovaAI - Kubernetes Secrets (Auto-generated from .env)
# ============================================================
# Generated on: $(date '+%Y-%m-%d %H:%M:%S')
# DO NOT COMMIT THIS FILE TO GIT!
# ============================================================
apiVersion: v1
kind: Secret
metadata:
  name: genovaai-secrets
  namespace: genovaai
type: Opaque
stringData:
  # Flask
  FLASK_SECRET_KEY: "$FLASK_SECRET_KEY"
  
  # PostgreSQL
  POSTGRES_USER: "genovaai"
  POSTGRES_PASSWORD: "$POSTGRES_PASSWORD"
  POSTGRES_DB: "genovaai"
  DATABASE_URL: "postgresql://genovaai:$POSTGRES_PASSWORD@postgres:5432/genovaai"
  
  # MongoDB (no auth for local dev)
  MONGO_INITDB_ROOT_USERNAME: "genovaai"
  MONGO_INITDB_ROOT_PASSWORD: "$MONGO_PASSWORD"
  MONGO_INITDB_DATABASE: "genovaai"
  MONGO_URI: "mongodb://mongodb:27017/genovaai"
  MONGODB_URI: "mongodb://mongodb:27017/genovaai"
  
  # Redis
  REDIS_PASSWORD: "$REDIS_PASSWORD"
  REDIS_URL: "redis://redis:6379/0"
  
  # RabbitMQ
  RABBITMQ_DEFAULT_USER: "genovaai"
  RABBITMQ_DEFAULT_PASS: "$RABBITMQ_PASSWORD"
  CELERY_BROKER_URL: "amqp://genovaai:$RABBITMQ_PASSWORD@rabbitmq:5672//"
  CELERY_RESULT_BACKEND: "redis://redis:6379/0"
  
  # Gemini API
  GEMINI_API_KEY: "$GEMINI_API_KEY"
  
  # LangSmith (optional)
  LANGCHAIN_API_KEY: "$LANGCHAIN_API_KEY"
  LANGCHAIN_PROJECT: "GenovaAI"
EOF

echo "✅ Generated: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  kubectl apply -k kubernetes-manifests/"
echo "  kubectl port-forward -n genovaai svc/genovaai 5000:5000"
echo ""
echo "Then open: http://localhost:5000"
