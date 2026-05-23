#!/usr/bin/env python3
"""bucket_simulator.py — replay a request trace through a token bucket and report projected 429s.

Trace CSV format (header required):
  timestamp_iso,endpoint,request_count

Example:
  2026-05-09T17:00:00Z,conversations,3
  2026-05-09T17:00:01Z,reviews,1

Usage:
  bucket_simulator.py --trace traces/2026-05-09-prod-replay.csv \\
                      --rate-per-minute 60 --capacity 10 \\
                      [--daily-quota 50000] [--output json|human]

Exit codes:
  0  simulation complete, zero projected 429s
  1  simulation complete, projected 429s > 0 (bucket undersized for this trace)
  2  trace file missing or unreadable
  3  trace file malformed (header missing or bad rows)
"""

from __future__ import annotations
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class SimulatedBucket:
    """Wall-clock-independent bucket. All time is the trace's timestamps."""

    def __init__(self, rate_per_minute: float, capacity: float):
        self.rate_per_sec = rate_per_minute / 60.0
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.last_refill_t = None  # set on first request

    def acquire_at(self, t_sec: float) -> float:
        """Return wait time in seconds for a request submitted at t_sec."""
        if self.last_refill_t is None:
            self.last_refill_t = t_sec
        else:
            elapsed = t_sec - self.last_refill_t
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)
            self.last_refill_t = t_sec
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return 0.0
        deficit = 1.0 - self.tokens
        wait_s = deficit / self.rate_per_sec
        # After the wait, we will have exactly 1 token; consume it.
        self.tokens = 0.0
        self.last_refill_t = t_sec + wait_s
        return wait_s


def parse_iso(s: str) -> float:
    # Accept Z or +00:00 forms
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return (
        datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()
        if datetime.fromisoformat(s).tzinfo is None
        else datetime.fromisoformat(s).timestamp()
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trace", required=True, type=Path)
    ap.add_argument("--rate-per-minute", type=float, default=60.0)
    ap.add_argument("--capacity", type=float, default=10.0)
    ap.add_argument(
        "--daily-quota", type=int, default=0, help="if > 0, report at which request the daily quota would exhaust"
    )
    ap.add_argument("--output", choices=("json", "human"), default="json")
    args = ap.parse_args()

    if not args.trace.exists():
        print(f"trace file not found: {args.trace}", file=sys.stderr)
        return 2

    try:
        with args.trace.open() as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or set(reader.fieldnames) < {"timestamp_iso", "endpoint", "request_count"}:
                print("trace missing required header (timestamp_iso,endpoint,request_count)", file=sys.stderr)
                return 3
            rows = list(reader)
    except Exception as e:
        print(f"could not read trace: {e}", file=sys.stderr)
        return 2

    bucket = SimulatedBucket(args.rate_per_minute, args.capacity)
    waits_ms: list[float] = []
    projected_429s = 0
    total_requests = 0
    quota_exhausted_at = None
    trace_start_t = None
    trace_end_t = None

    for i, row in enumerate(rows):
        try:
            t = parse_iso(row["timestamp_iso"])
            count = int(row["request_count"])
        except Exception as e:
            print(f"row {i + 2}: bad value: {e}", file=sys.stderr)
            return 3
        if trace_start_t is None:
            trace_start_t = t
        trace_end_t = t
        for _ in range(count):
            wait_s = bucket.acquire_at(t)
            waits_ms.append(wait_s * 1000.0)
            # If wait exceeded 120s, the retry-wrapper would have given up — count as 429
            if wait_s > 120.0:
                projected_429s += 1
            total_requests += 1
            if args.daily_quota and total_requests >= args.daily_quota and quota_exhausted_at is None:
                quota_exhausted_at = total_requests

    waits_ms.sort()
    p50 = waits_ms[len(waits_ms) // 2] if waits_ms else 0.0
    p99 = waits_ms[int(len(waits_ms) * 0.99)] if waits_ms else 0.0
    window_s = (trace_end_t - trace_start_t) if trace_start_t and trace_end_t else 0.0

    report = {
        "trace_requests": total_requests,
        "trace_window_seconds": round(window_s, 2),
        "projected_429_count": projected_429s,
        "projected_p50_queue_wait_ms": round(p50, 1),
        "projected_p99_queue_wait_ms": round(p99, 1),
        "would_exhaust_daily_quota_at_request": quota_exhausted_at,
    }

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        for k, v in report.items():
            print(f"{k}: {v}")

    return 1 if projected_429s > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
