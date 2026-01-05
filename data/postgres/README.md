# PostgreSQL Data Directory
This directory contains PostgreSQL data when running with Docker Compose.

**⚠️ WARNING:** Do not delete this directory if you have data you want to keep!

## Backup

To backup your PostgreSQL data:
```bash
./scripts/backup_postgres.sh ./backups
```

## Restore

To restore from a backup:
```bash
gunzip ./backups/genovaai_backup_YYYYMMDD_HHMMSS.sql.gz
docker exec -i genovaai-postgres psql -U genovaai_user -d genovaai < ./backups/genovaai_backup_YYYYMMDD_HHMMSS.sql
```
