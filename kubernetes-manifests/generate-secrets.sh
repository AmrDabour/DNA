#!/bin/bash
# ============================================================
# GenovaAI - Generate Kubernetes Secrets from Environment
# ============================================================
# This script generates the secrets.yaml file from the template
# by substituting placeholders with actual values from environment
# variables or GitHub Secrets.
#
# Usage:
#   ./generate-secrets.sh
#
# Required environment variables:
#   - FLASK_SECRET_KEY
#   - POSTGRES_PASSWORD
#   - MONGO_PASSWORD
#   - REDIS_PASSWORD
#   - RABBITMQ_PASSWORD
#   - GEMINI_API_KEY
#   - LANGCHAIN_API_KEY (optional, defaults to empty)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/secrets.template.yaml"
OUTPUT_FILE="$SCRIPT_DIR/secrets.generated.yaml"

# Check required variables
required_vars=(
    "FLASK_SECRET_KEY"
    "POSTGRES_PASSWORD"
    "MONGO_PASSWORD"
    "REDIS_PASSWORD"
    "RABBITMQ_PASSWORD"
    "GEMINI_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables before running this script."
    echo "Example:"
    echo "  export GEMINI_API_KEY='your-api-key'"
    exit 1
fi

# Set defaults for optional variables
LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-}"

echo "🔐 Generating Kubernetes secrets..."

# Copy template and substitute placeholders
cp "$TEMPLATE_FILE" "$OUTPUT_FILE"

# Substitute placeholders
sed -i "s|{{FLASK_SECRET_KEY}}|${FLASK_SECRET_KEY}|g" "$OUTPUT_FILE"
sed -i "s|{{POSTGRES_PASSWORD}}|${POSTGRES_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|{{MONGO_PASSWORD}}|${MONGO_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|{{REDIS_PASSWORD}}|${REDIS_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|{{RABBITMQ_PASSWORD}}|${RABBITMQ_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|{{GEMINI_API_KEY}}|${GEMINI_API_KEY}|g" "$OUTPUT_FILE"
sed -i "s|{{LANGCHAIN_API_KEY}}|${LANGCHAIN_API_KEY}|g" "$OUTPUT_FILE"

echo "✅ Secrets generated: $OUTPUT_FILE"
echo ""
echo "⚠️  IMPORTANT: Do NOT commit $OUTPUT_FILE to git!"
echo "    It contains sensitive information."
echo ""
echo "To apply secrets to Kubernetes:"
echo "  kubectl apply -f $OUTPUT_FILE"
