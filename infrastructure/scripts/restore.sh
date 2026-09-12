#!/usr/bin/env bash
# Restore a WorkTrack PostgreSQL backup created by backup.sh.
# Usage:   ./infrastructure/scripts/restore.sh ./backups/worktrack_YYYYMMDD_HHMMSS.sql.gz
set -euo pipefail

FILE="${1:?usage: restore.sh <backup.sql.gz>}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
DB_USER="${POSTGRES_USER:-worktrack}"
DB_NAME="${POSTGRES_DB:-worktrack}"

echo "[restore] WARNING: this overwrites data in '$DB_NAME'. Ctrl-C to abort."
sleep 3
echo "[restore] restoring from $FILE"
gunzip -c "$FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$DB_USER" -d "$DB_NAME"
echo "[restore] done."
