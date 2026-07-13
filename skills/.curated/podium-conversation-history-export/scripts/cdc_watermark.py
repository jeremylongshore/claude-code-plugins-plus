#!/usr/bin/env python3
"""cdc_watermark.py — inspect, reset, or advance the CDC watermark.

The watermark is a single Unix timestamp per resource. It represents the
last successful `updated_at` covered by a completed incremental pass.
Resetting forces a full re-pull on the next run; advancing manually skips
ahead (use only after an external backfill).

Usage:
  # Inspect all resources
  cdc_watermark.py --db ./watermarks.sqlite

  # Inspect one resource
  cdc_watermark.py --db ./watermarks.sqlite --resource conversations

  # Reset (force full re-pull on next run)
  cdc_watermark.py --db ./watermarks.sqlite --resource conversations --reset --confirm

  # Advance manually to a specific Unix timestamp
  cdc_watermark.py --db ./watermarks.sqlite --resource conversations --advance 1715212800

Exit codes:
  0  success
  1  ERR_EXPORT_014 — --reset without --confirm
  2  database / IO error
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone


def open_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS cdc(resource TEXT PRIMARY KEY, watermark REAL, updated_at REAL)")
    return con


def inspect_all(db_path: str) -> dict:
    con = open_db(db_path)
    rows = con.execute("SELECT resource, watermark, updated_at FROM cdc ORDER BY resource").fetchall()
    con.close()
    now = time.time()
    return {
        r: {
            "watermark": wm,
            "iso8601": datetime.fromtimestamp(wm, tz=timezone.utc).isoformat() if wm else None,
            "age_seconds": int(now - wm) if wm else None,
            "last_advanced_at": datetime.fromtimestamp(ua, tz=timezone.utc).isoformat() if ua else None,
        }
        for (r, wm, ua) in rows
    }


def inspect_one(db_path: str, resource: str) -> dict:
    con = open_db(db_path)
    row = con.execute("SELECT watermark, updated_at FROM cdc WHERE resource = ?", (resource,)).fetchone()
    con.close()
    if not row:
        return {resource: None}
    wm, ua = row
    now = time.time()
    return {
        resource: {
            "watermark": wm,
            "iso8601": datetime.fromtimestamp(wm, tz=timezone.utc).isoformat(),
            "age_seconds": int(now - wm),
            "last_advanced_at": datetime.fromtimestamp(ua, tz=timezone.utc).isoformat() if ua else None,
        }
    }


def reset(db_path: str, resource: str) -> None:
    con = open_db(db_path)
    con.execute("DELETE FROM cdc WHERE resource = ?", (resource,))
    con.commit()
    con.close()


def advance(db_path: str, resource: str, ts: float) -> None:
    con = open_db(db_path)
    con.execute(
        """
        INSERT INTO cdc(resource, watermark, updated_at) VALUES(?, ?, ?)
        ON CONFLICT(resource) DO UPDATE SET watermark = excluded.watermark, updated_at = excluded.updated_at
    """,
        (resource, ts, time.time()),
    )
    con.commit()
    con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True, help="SQLite watermark store path")
    ap.add_argument("--resource", help="resource name (conversations|reviews|contacts); omit to list all")
    ap.add_argument("--reset", action="store_true", help="reset watermark (force full re-pull)")
    ap.add_argument("--confirm", action="store_true", help="required for destructive operations")
    ap.add_argument("--advance", type=float, help="manually advance watermark to this Unix timestamp")
    args = ap.parse_args()

    try:
        if args.reset:
            if not args.resource:
                print("--reset requires --resource", file=sys.stderr)
                return 2
            if not args.confirm:
                print(
                    "ERR_EXPORT_014 --reset requires --confirm (forces a full re-pull, burns rate-limit budget)",
                    file=sys.stderr,
                )
                return 1
            reset(args.db, args.resource)
            print(json.dumps({"action": "reset", "resource": args.resource, "ok": True}))
            return 0

        if args.advance is not None:
            if not args.resource:
                print("--advance requires --resource", file=sys.stderr)
                return 2
            advance(args.db, args.resource, args.advance)
            print(json.dumps({"action": "advance", "resource": args.resource, "watermark": args.advance}))
            return 0

        if args.resource:
            print(json.dumps(inspect_one(args.db, args.resource), indent=2))
        else:
            print(json.dumps(inspect_all(args.db), indent=2))
        return 0

    except sqlite3.OperationalError as e:
        print(f"ERR_EXPORT_005 watermark DB error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"unhandled error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
