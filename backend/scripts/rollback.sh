#!/usr/bin/env bash
# SiraFit rollback helper.
#
# Downgrades the database schema by N migrations (default 1) using Alembic,
# then restarts the API/worker services so they pick up the older schema.
#
# Usage:
#   ./rollback.sh         # downgrade 1 revision
#   ./rollback.sh 3       # downgrade 3 revisions
#   ./rollback.sh base    # downgrade to empty schema (DANGEROUS)
#
# Preconditions:
#   - Run from a checkout with `migrations/` and `alembic.ini` (i.e. the backend dir).
#   - DATABASE_URL points at the target database.
set -euo pipefail

REV="${1:-1}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # change into the backend directory

echo "[rollback] Downgrading database by: $REV"
alembic downgrade "-$REV" 2>/dev/null || alembic downgrade "$REV"

echo "[rollback] Restarting services"
if command -v docker >/dev/null 2>&1 && docker compose ps >/dev/null 2>&1; then
  docker compose restart backend celery_worker celery_beat
else
  echo "[rollback] docker compose not detected; restart the API/worker processes manually."
fi

echo "[rollback] Done. Verify with: python scripts/healthcheck.sh"
