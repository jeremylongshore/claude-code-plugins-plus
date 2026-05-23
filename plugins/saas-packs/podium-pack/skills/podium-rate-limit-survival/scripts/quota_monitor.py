#!/usr/bin/env python3
"""quota_monitor.py — query the daily Podium quota counter and emit warn/page/throttle.

Reads `podium:quota:YYYY-MM-DD` from Redis (or a SQLite fallback) and compares
against the configured daily quota. Prints a structured JSON report on stdout.

Usage:
  quota_monitor.py --redis-url "$PODIUM_RATE_LIMIT_REDIS_URL" --quota 50000
  quota_monitor.py --sqlite-path ./.podium-quota.db    --quota 50000

Thresholds (configurable):
  --warn-threshold     0.70   (warn      — exit 1)
  --page-threshold     0.85   (page      — exit 2)
  --throttle-threshold 0.95   (throttle  — exit 3)

Exit codes:
  0  below warn (< 70%)
  1  warn      (70%-84%)
  2  page      (85%-94%)
  3  throttle  (>= 95%)
  4  could not read counter store
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_from_redis(url: str) -> int:
    try:
        import redis
    except ImportError:
        print("redis package not installed; try: pip install redis", file=sys.stderr)
        raise
    client = redis.from_url(url, decode_responses=True)
    key = f"podium:quota:{today_utc()}"
    val = client.get(key)
    return int(val) if val is not None else 0


def read_from_sqlite(path: str) -> int:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT count FROM quota WHERE day = ?", (today_utc(),)).fetchone()
        return row[0] if row else 0


def tier(ratio: float, warn: float, page: float, throttle: float) -> tuple[str, int]:
    if ratio >= throttle:
        return ("throttle", 3)
    if ratio >= page:
        return ("page", 2)
    if ratio >= warn:
        return ("warn", 1)
    return ("ok", 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--redis-url")
    src.add_argument("--sqlite-path")
    ap.add_argument("--quota", type=int, required=True)
    ap.add_argument("--warn-threshold", type=float, default=0.70)
    ap.add_argument("--page-threshold", type=float, default=0.85)
    ap.add_argument("--throttle-threshold", type=float, default=0.95)
    args = ap.parse_args()

    try:
        if args.redis_url:
            count = read_from_redis(args.redis_url)
            backend = "redis"
        else:
            count = read_from_sqlite(args.sqlite_path)
            backend = "sqlite"
    except Exception as e:
        print(f"could not read counter store: {e}", file=sys.stderr)
        return 4

    ratio = count / args.quota if args.quota > 0 else 0.0
    tier_name, exit_code = tier(ratio, args.warn_threshold, args.page_threshold, args.throttle_threshold)

    report = {
        "day_utc": today_utc(),
        "backend": backend,
        "count": count,
        "quota": args.quota,
        "ratio": round(ratio, 4),
        "tier": tier_name,
    }
    print(json.dumps(report))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
