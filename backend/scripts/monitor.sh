#!/usr/bin/env bash
# SiraFit alerting wrapper.
#
# Runs the healthcheck every invocation (intended to be scheduled via cron,
# e.g. * * * * * /path/to/monitor.sh >> /var/log/sirafit/monitor.log 2>&1).
# On failure it notifies via webhook (ALERT_WEBHOOK) and/or email (ALERT_EMAIL).
#
# Env overrides:
#   ALERT_WEBHOOK  - HTTPS URL that accepts a JSON POST {"text": "..."}
#   ALERT_EMAIL    - recipient address (requires `mail`/sendmail)
#   ALERT_HOST     - label for the failing environment (default "sirafit")
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_HOST="${ALERT_HOST:-sirafit}"

if "$SCRIPT_DIR/healthcheck.sh"; then
  exit 0
fi

MSG="SiraFit [$ALERT_HOST] health check FAILED at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "$MSG"

if [ -n "$ALERT_WEBHOOK" ]; then
  curl -fsS --max-time 10 -X POST "$ALERT_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"$MSG\"}" || echo "webhook alert failed"
fi

if [ -n "$ALERT_EMAIL" ]; then
  echo "$MSG" | mail -s "SiraFit ALERT: health check failed" "$ALERT_EMAIL" \
    || echo "email alert failed (is 'mail' configured?)"
fi

exit 1
