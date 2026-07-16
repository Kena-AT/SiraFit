#!/usr/bin/env bash
# SiraFit readiness probe.
#
# Exits non-zero when the service is not ready so it can be used directly as a
# monitoring/alerting trigger (cron, Kubernetes probe, load-balancer check).
#
# Uses Python's stdlib so it works without curl/wget installed.
# Env overrides:
#   HEALTH_BASE_URL (default http://localhost:8000)
set -uo pipefail

BASE_URL="${HEALTH_BASE_URL:-http://localhost:8000}"

python - "$BASE_URL" <<'PY'
import sys, json, urllib.request
base = sys.argv[1]
try:
    with urllib.request.urlopen(f"{base}/health/ready", timeout=5) as r:
        body = json.loads(r.read().decode())
except Exception as exc:
    print(f"healthcheck FAILED: cannot reach {base}/health/ready ({exc})")
    sys.exit(1)

if body.get("ready") is not True:
    print(f"healthcheck FAILED: {json.dumps(body)}")
    sys.exit(1)

print("healthcheck OK")
sys.exit(0)
PY
