#!/usr/bin/env bash
# SiraFit database backup script (Sprint 15 Production Hardened).
#
# Features:
#   - Concurrency protection using lockfile / flock
#   - Full PostgreSQL dump & compression
#   - Immediate integrity verification (gzip -t)
#   - Optional symmetric encryption when BACKUP_ENCRYPTION_KEY is provided
#   - Offsite upload verification (AWS S3)
#   - Strict retention rotation
#   - Observable exit codes, duration, and metrics
#
# Usage:
#   DATABASE_URL=postgres://user:pass@host:5432/sirafit ./backup.sh
#
# Env overrides:
#   BACKUP_DIR (default /var/backups/sirafit)
#   RETENTION_DAYS (default 14)
#   S3_BUCKET (optional; enables upload)
#   BACKUP_ENCRYPTION_KEY (optional; symmetric encryption)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/sirafit}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
S3_BUCKET="${S3_BUCKET:-}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DB_URL="${DATABASE_URL:?DATABASE_URL must be set (postgres://user:pass@host:5432/db)}"

mkdir -p "$BACKUP_DIR"
LOCKFILE="$BACKUP_DIR/.backup.lock"

# 1. Concurrency check (flock or directory lock)
exec 200>"$LOCKFILE"
if ! command -v flock >/dev/null 2>&1 || ! flock -n 200; then
  if [ -f "$LOCKFILE.pid" ]; then
    PID=$(cat "$LOCKFILE.pid" 2>/dev/null || true)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
      echo "[backup] ERROR: Backup already in progress (PID: $PID). Aborting." >&2
      exit 1
    fi
  fi
fi
echo "$$" > "$LOCKFILE.pid"
trap 'rm -f "$LOCKFILE.pid"' EXIT

START_TIME=$(date +%s)
OUT="$BACKUP_DIR/sirafit-$TIMESTAMP.sql.gz"

echo "[backup] Starting PostgreSQL dump -> $OUT"
pg_dump "$DB_URL" | gzip > "$OUT"

# 2. Archive integrity verification
echo "[backup] Verifying archive integrity..."
if ! gzip -t "$OUT"; then
  echo "[backup] FATAL: Archive integrity check failed for $OUT" >&2
  rm -f "$OUT"
  exit 2
fi
echo "[backup] Archive integrity verified successfully."

FINAL_PAYLOAD="$OUT"

# 3. Optional Encryption
if [ -n "$BACKUP_ENCRYPTION_KEY" ]; then
  ENC_OUT="$OUT.enc"
  echo "[backup] Encrypting backup with OpenSSL AES-256-CBC..."
  openssl enc -aes-256-cbc -salt -pbkdf2 -in "$OUT" -out "$ENC_OUT" -k "$BACKUP_ENCRYPTION_KEY"
  rm -f "$OUT"
  FINAL_PAYLOAD="$ENC_OUT"
  echo "[backup] Encrypted payload created: $FINAL_PAYLOAD"
fi

FILESIZE=$(wc -c < "$FINAL_PAYLOAD" | tr -d ' ')
echo "[backup] Backup file size: $FILESIZE bytes"

# 4. Off-site upload and verification
if [ -n "$S3_BUCKET" ]; then
  echo "[backup] Uploading to s3://$S3_BUCKET/$(basename "$FINAL_PAYLOAD")"
  aws s3 cp "$FINAL_PAYLOAD" "s3://$S3_BUCKET/"
  
  echo "[backup] Verifying remote upload..."
  if ! aws s3 ls "s3://$S3_BUCKET/$(basename "$FINAL_PAYLOAD")" >/dev/null 2>&1; then
    echo "[backup] ERROR: Remote verification failed for s3://$S3_BUCKET/$(basename "$FINAL_PAYLOAD")" >&2
    exit 3
  fi
  echo "[backup] Remote upload verified."
fi

# 5. Retention rotation
echo "[backup] Rotating backups older than $RETENTION_DAYS days in $BACKUP_DIR"
find "$BACKUP_DIR" \( -name 'sirafit-*.sql.gz' -o -name 'sirafit-*.sql.gz.enc' \) -mtime "+$RETENTION_DAYS" -delete

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "[backup] Backup process completed in ${DURATION}s. Path: $FINAL_PAYLOAD"
