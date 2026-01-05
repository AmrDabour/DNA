#!/bin/bash
# ============================================================
# PostgreSQL Backup Script for GenovaAI
# Usage: ./scripts/backup_postgres.sh [backup_dir]
# ============================================================

set -e

# Configuration
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/genovaai_backup_${TIMESTAMP}.sql"

# Database configuration (from environment or defaults)
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-genovaai}"
POSTGRES_USER="${POSTGRES_USER:-genovaai_user}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "=============================================="
echo "🗄️  GenovaAI PostgreSQL Backup"
echo "=============================================="
echo "Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "Database: ${POSTGRES_DB}"
echo "User: ${POSTGRES_USER}"
echo "Backup file: ${BACKUP_FILE}"
echo "=============================================="

# Perform backup
echo "📦 Starting backup..."

if command -v pg_dump &> /dev/null; then
    # Local pg_dump
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -F p \
        -f "${BACKUP_FILE}"
elif command -v docker &> /dev/null; then
    # Docker-based backup
    docker exec genovaai-postgres pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -F p > "${BACKUP_FILE}"
else
    echo "❌ Error: pg_dump not found and Docker not available"
    exit 1
fi

# Compress backup
echo "🗜️  Compressing backup..."
gzip "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Calculate size
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)

echo "=============================================="
echo "✅ Backup completed successfully!"
echo "File: ${BACKUP_FILE}"
echo "Size: ${BACKUP_SIZE}"
echo "=============================================="

# Optional: Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups (keeping last 7 days)..."
find "${BACKUP_DIR}" -name "genovaai_backup_*.sql.gz" -mtime +7 -delete 2>/dev/null || true

echo "✅ Done!"
