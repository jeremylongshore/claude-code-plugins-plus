#!/usr/bin/env python3
"""cooldown_check.py — query the cooldown state for a single phone.

Usage:
  cooldown_check.py --phone "+61412345678" --redis-url "$REDIS_URL"
  cooldown_check.py --phone "+61412345678" --sqlite-path /var/lib/podium/cooldown.db

Output:
  JSON on stdout with last_contact_at, cooldown_days_remaining, can_send.

Exit codes:
  0  can_send=true OR phone has no record
  1  can_send=false (in cooldown)
  2  backend unreachable or invalid args
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
import sqlite3


def query_redis(redis_url: str, phone: str, cooldown_days: int) -> dict:
    try:
        import redis as redis_lib
    except ImportError:
        print("redis package not installed; pip install redis", file=sys.stderr)
        sys.exit(2)
    r = redis_lib.from_url(redis_url, decode_responses=True)
    key = f"podium:cooldown:{phone}"
    last = r.get(key)
    if last is None:
        return {"phone": phone, "last_contact_at": None, "cooldown_days_remaining": 0.0, "can_send": True}
    last_f = float(last)
    cooldown_seconds = cooldown_days * 86400
    remaining_seconds = cooldown_seconds - (time.time() - last_f)
    return {
        "phone": phone,
        "last_contact_at": last_f,
        "cooldown_days_remaining": max(0.0, remaining_seconds / 86400),
        "can_send": remaining_seconds <= 0,
    }


def query_sqlite(db_path: str, phone: str, cooldown_days: int) -> dict:
    if not os.path.exists(db_path):
        return {"phone": phone, "last_contact_at": None, "cooldown_days_remaining": 0.0, "can_send": True}
    c = sqlite3.connect(db_path, timeout=5)
    row = c.execute("SELECT last_contact_at FROM cooldown WHERE phone = ?", (phone,)).fetchone()
    c.close()
    if row is None:
        return {"phone": phone, "last_contact_at": None, "cooldown_days_remaining": 0.0, "can_send": True}
    last_f = row[0]
    cooldown_seconds = cooldown_days * 86400
    remaining_seconds = cooldown_seconds - (time.time() - last_f)
    return {
        "phone": phone,
        "last_contact_at": last_f,
        "cooldown_days_remaining": max(0.0, remaining_seconds / 86400),
        "can_send": remaining_seconds <= 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", required=True, help="E.164 phone (e.g. +61412345678)")
    ap.add_argument("--cooldown-days", type=int, default=30)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--redis-url")
    g.add_argument("--sqlite-path")
    args = ap.parse_args()

    if not args.phone.startswith("+"):
        print(f"phone must be E.164 (got: {args.phone})", file=sys.stderr)
        return 2

    try:
        if args.redis_url:
            result = query_redis(args.redis_url, args.phone, args.cooldown_days)
        else:
            result = query_sqlite(args.sqlite_path, args.phone, args.cooldown_days)
    except Exception as e:
        print(f"backend error: {e}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["can_send"] else 1


if __name__ == "__main__":
    sys.exit(main())
