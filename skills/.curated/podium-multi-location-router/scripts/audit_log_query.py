#!/usr/bin/env python3
"""audit_log_query.py — query the multi-location router audit log by location_uid,
date range, status, or endpoint. Emits matched records as JSONL or human-readable.

Usage:
  audit_log_query.py --audit-log ./audit-log/podium-router.jsonl \\
                     [--location-uid {your-location-uid}] \\
                     [--since 2026-05-01] \\
                     [--until 2026-05-31] \\
                     [--status 200] \\
                     [--endpoint /v4/contacts] \\
                     [--request-id <hex>] \\
                     [--output json|human|count]

Exit codes:
  0  at least one matching record was found
  1  no matching records
  2  audit log unreadable or malformed
"""

from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_date(s: str) -> float:
    # Accept YYYY-MM-DD or ISO8601 with timezone. Naive dates assumed UTC.
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    raise ValueError(f"unparseable date: {s}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit-log", required=True, type=Path)
    ap.add_argument("--location-uid", default=None)
    ap.add_argument("--since", default=None, help="YYYY-MM-DD or ISO8601")
    ap.add_argument("--until", default=None, help="YYYY-MM-DD or ISO8601")
    ap.add_argument("--status", type=int, default=None)
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--request-id", default=None)
    ap.add_argument("--output", choices=("json", "human", "count"), default="json")
    args = ap.parse_args()

    if not args.audit_log.exists():
        print(f"audit log not found: {args.audit_log}", file=sys.stderr)
        return 2

    try:
        since_ts = parse_date(args.since) if args.since else 0.0
        until_ts = parse_date(args.until) if args.until else time.time() + 1
    except ValueError as e:
        print(f"bad date: {e}", file=sys.stderr)
        return 2

    matched: list[dict] = []
    with args.audit_log.open() as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"audit log malformed at line {lineno}: {e}", file=sys.stderr)
                return 2

            if args.location_uid and rec.get("location_uid") != args.location_uid:
                continue
            if args.status is not None and rec.get("status") != args.status:
                continue
            if args.endpoint and rec.get("endpoint") != args.endpoint:
                continue
            if args.request_id and rec.get("request_id") != args.request_id:
                continue
            ts = rec.get("ts", 0)
            if ts < since_ts or ts >= until_ts:
                continue
            matched.append(rec)

    if args.output == "count":
        print(len(matched))
    elif args.output == "json":
        for rec in matched:
            print(json.dumps(rec))
    else:
        for rec in matched:
            ts_str = datetime.fromtimestamp(rec["ts"], tz=timezone.utc).isoformat()
            print(
                f"{ts_str}  uid={rec['location_uid']}  org={rec['org_slug']}  "
                f"{rec['method']:6s} {rec['endpoint']:40s}  status={rec['status']}  "
                f"latency={rec['latency_ms']}ms  req={rec['request_id']}"
            )

    return 0 if matched else 1


if __name__ == "__main__":
    sys.exit(main())
