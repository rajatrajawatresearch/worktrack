#!/usr/bin/env bash
# Daily PostgreSQL backup for WorkTrack (Docker Compose based).
# Usage:   ./infrastructure/scripts/backup.sh
# Cron:    0 2 * * *  cd /opt/worktrack && ./infrastructure/scripts/backup.sh >> /var/log/worktrack-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
DB_USER="${POSTGRES_USER:-worktrack}"
DB_NAME="${POSTGRES_DB:-worktrack}"

mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/worktrack_${TS}.sql.gz"

echo "[backup] dumping $DB_NAME -> $OUT"
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT"

echo "[backup] pruning backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'worktrack_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete || true

echo "[backup] done: $OUT"
