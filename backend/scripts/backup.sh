#!/usr/bin/env bash
# SiraFit database backup script.
#
# Dumps the PostgreSQL database to a timestamped, compressed file, rotates old
# backups, and optionally uploads to S3 when AWS CLI + S3_BUCKET are configured.
#
# Usage:
#   DATABASE_URL=postgres://user:pass@host:5432/sirafit ./backup.sh
#
# Env overrides:
#   BACKUP_DIR (default /var/backups/sirafit)
#   RETENTION_DAYS (default 14)
#   S3_BUCKET (optional; enables upload)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/sirafit}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
S3_BUCKET="${S3_BUCKET:-}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DB_URL="${DATABASE_URL:?DATABASE_URL must be set (postgres://user:pass@host:5432/db)}"

mkdir -p "$BACKUP_DIR"
OUT="$BACKUP_DIR/sirafit-$TIMESTAMP.sql.gz"

echo "[backup] Dumping database -> $OUT"
pg_dump "$DB_URL" | gzip > "$OUT"

if [ -n "$S3_BUCKET" ]; then
  echo "[backup] Uploading to s3://$S3_BUCKET"
  aws s3 cp "$OUT" "s3://$S3_BUCKET/"
fi

echo "[backup] Rotating backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name 'sirafit-*.sql.gz' -mtime "+$RETENTION_DAYS" -delete

echo "[backup] Done: $OUT"
