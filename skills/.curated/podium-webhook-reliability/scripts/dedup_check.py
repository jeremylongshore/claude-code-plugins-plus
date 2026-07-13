#!/usr/bin/env python3
"""dedup_check.py — check whether an event_id is already in the Podium webhook dedup cache.

Read-only inspection. Does NOT mutate the cache. Useful for confirming whether
a specific event_id was already processed (and would be rejected as a duplicate
on replay) before a manual replay.

Usage:
  dedup_check.py --event-id evt_<your-event-identifier> \\
                 [--redis-url redis://localhost:6379/0] \\
                 [--key-prefix podium:evt:]

Exit codes:
  0  first sight — event_id is NOT cached; a replay would be dispatched
  1  duplicate  — event_id IS cached; a replay would be rejected as duplicate
  2  backend unreachable / configuration error
"""

from __future__ import annotations
import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--redis-url", default=os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    ap.add_argument("--key-prefix", default="podium:evt:")
    args = ap.parse_args()

    try:
        import redis  # type: ignore
    except ImportError:
        print("ERR_WHK_CFG redis package not installed — `pip install redis`", file=sys.stderr)
        return 2

    try:
        r = redis.from_url(args.redis_url, decode_responses=True)
        r.ping()
    except Exception as e:
        print(f"ERR_WHK_006 dedup_backend_unavailable: {e}", file=sys.stderr)
        return 2

    key = f"{args.key_prefix}{args.event_id}"
    try:
        exists = r.exists(key)
        ttl = r.ttl(key) if exists else None
    except Exception as e:
        print(f"ERR_WHK_006 dedup query failed: {e}", file=sys.stderr)
        return 2

    if exists:
        print(f"duplicate: key={key} ttl_remaining={ttl}s", file=sys.stderr)
        return 1
    print(f"first_sight: key={key} (not cached)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
