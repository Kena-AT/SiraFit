#!/usr/bin/env python3
"""Report Celery queue depths (including the dead-letter queue) for monitoring.

Connects to the broker (Redis) and prints the pending message count for every
SiraFit queue so operators can spot backlogs or dead-lettered tasks that need
replay.

Usage:
    REDIS_URL=redis://localhost:6379/0 python scripts/inspect_celery_queues.py
"""

import os
import sys

try:
    import redis
except ImportError:  # pragma: no cover
    sys.exit("The 'redis' package is required: pip install redis")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUEUES = [
    "sirafit",
    "resume_generation",
    "pdf_rendering",
    "batch_processing",
    "notifications",
    "sirafit_dlq",
]


def main() -> int:
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    print(f"Celery queue depths (broker: {REDIS_URL})")
    dlq_depth = 0
    for q in QUEUES:
        try:
            depth = client.llen(q)
        except Exception as exc:  # pragma: no cover
            depth = f"error: {exc}"
        is_dlq = q == "sirafit_dlq"
        if is_dlq and isinstance(depth, int):
            dlq_depth = depth
        print(f"  {q:20s} {depth}{'  <-- DLQ' if is_dlq else ''}")
    if dlq_depth:
        print(f"\nWARNING: {dlq_depth} task(s) dead-lettered. Inspect and replay as needed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
