# SiraFit — Production Runbook (Sprint 12)

This runbook covers the operational procedures for running SiraFit in
production after the Sprint 12 hardening work: Redis-backed rate limiting, a
Redis caching layer, Celery dead-letter handling, and observability/backup
tooling.

## 1. Deployment

- **API**: `backend/Dockerfile` runs `uvicorn app.main:app` with
  `--proxy-headers` (set `FORWARDED_ALLOW_IPS=*` behind a TLS-terminating proxy).
  Auto-reload is disabled in the image — never use `--reload` in production.
- **Worker / beat**: `backend/Dockerfile.celery`. Beat schedules
  `check_reminders_task`.
- **Compose**: `docker-compose.yml` now declares healthchecks for `postgres`,
  `redis`, and `backend`, and uses `depends_on: condition: service_healthy` so
  the API and workers only start once their dependencies are healthy.

Required environment variables (see `.env` / `render.yaml`):
`DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, `CELERY_BROKER_URL`,
`CELERY_RESULT_BACKEND`, `SMTP_*`, `CORS_ORIGINS`, `ENVIRONMENT=production`.

## 2. Rate limiting

Rate limiting is a global FastAPI middleware (`app.core.rate_limiting`). It is
**disabled in `testing`/`development`** and enforced only in `production`.

- Counter lives in **Redis** (`ratelimit:<type>:<user|ip>`) when Redis is
  reachable, otherwise an in-process fallback is used (single-instance only).
- Limits (max requests / window): `auth_login` 5/300s, `auth_register` 3/3600s,
  `auth_verify_email` 5/300s, `auth_forgot_password` 3/3600s, `auth_refresh`
  10/60s, `api_read` 100/60s, `api_write` 30/60s, `api_import` 10/60s.
- Keyed by authenticated user (from the bearer token) when present, else by IP.
- Exceeding a limit returns `429` with `Retry-After` and `X-RateLimit-*` headers.

## 3. Caching

`app.core.cache` caches expensive read responses (analytics metrics, dashboard
stats) in Redis with a short TTL, falling back to in-process memory when Redis
is unavailable. Caching is a **no-op in `testing`** to keep the suite
deterministic. Invalidate on writes (e.g. creating an analytics snapshot drops
the user's cached metrics).

## 4. Monitoring

- **Liveness**: `GET /health/live` — always returns `{"alive": true}`.
- **Readiness**: `GET /health/ready` — checks DB; reports Redis as
  `connected`/`disabled`. Returns `ready: false` on failure.
- **Metrics**: `GET /metrics` — Prometheus scrape target exposing process and
  HTTP request counters (`http_requests_total`, `http_requests_in_progress`).
  Point Prometheus/Grafana here. The endpoint is excluded from rate limiting.
- **Queue depth**: `python backend/scripts/inspect_celery_queues.py`
  (requires `REDIS_URL`) prints pending counts for every queue, including the
  DLQ, and exits non-zero if anything is dead-lettered.

## 5. Alerting

`backend/scripts/monitor.sh` runs `healthcheck.sh` and, on failure, posts to
`ALERT_WEBHOOK` (JSON) and/or emails `ALERT_EMAIL`. Schedule it from cron:

```
* * * * * /opt/sirafit/backend/scripts/monitor.sh >> /var/log/sirafit/monitor.log 2>&1
```

Configure `ALERT_WEBHOOK` (e.g. Slack/Teams incoming webhook) and `ALERT_EMAIL`
in the cron environment.

## 6. Backup & restore

`backend/scripts/backup.sh` dumps the database with `pg_dump`, compresses it,
rotates backups older than `RETENTION_DAYS` (default 14), and optionally uploads
to S3 when `S3_BUCKET` is set.

```bash
DATABASE_URL=postgres://u:p@host:5432/sirafit \
BACKUP_DIR=/var/backups/sirafit S3_BUCKET=my-bucket \
  backend/scripts/backup.sh
```

Restore:

```bash
gunzip -c /var/backups/sirafit/sirafit-<ts>.sql.gz | psql "$DATABASE_URL"
```

Schedule backups (e.g. daily at 02:00):

```
0 2 * * * DATABASE_URL=... backend/scripts/backup.sh
```

## 7. Rollback

If a deploy causes problems:

1. Revert the code (`git revert <sha>` / redeploy previous image).
2. If a database migration is involved, downgrade the schema:
   `backend/scripts/rollback.sh [revisions]` (default 1; `base` for full reset).
3. `docker compose restart backend celery_worker celery_beat` (the script does
   this automatically when run inside a compose deployment).
4. Verify: `python backend/scripts/healthcheck.sh`.

## 8. Celery dead-letter queue

Tasks carry `max_retries` (resume 3, PDF 2, batch 3, notifications 3). When a
task exhausts its retries, `BaseRetryTask.on_failure` re-publishes it to the
`sirafit_dlq` queue via the `handle_dead_letter` collector task, which logs the
failure for inspection.

Inspect and replay:

```bash
python backend/scripts/inspect_celery_queues.py   # see DLQ depth
# Replay a dead-lettered task by re-enqueuing its payload onto the original queue,
# or fix the root cause and re-run the business operation from the API.
```

Tasks use `acks_late=True` + `task_reject_on_worker_lost=True`, so a worker
crash does not lose a job — it is redelivered.
