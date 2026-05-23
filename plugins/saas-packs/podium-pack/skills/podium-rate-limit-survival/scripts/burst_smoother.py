#!/usr/bin/env python3
"""burst_smoother.py — smooth a CSV batch of requests over a target window.

Input CSV format (header required):
  timestamp_iso,endpoint,request_count

Output CSV format:
  scheduled_at_iso,endpoint,request_index

Computes per-request delay = max(target_window/N, 60/rate_per_minute). Bucket rate
dominates on small N; target window dominates on large N. The output schedule
respects whichever is slower so the bucket cannot be over-driven.

Usage:
  burst_smoother.py --input pending-reviews.csv \\
                    --rate-per-minute 15 \\
                    --target-window-seconds 120 \\
                    --output smoothed-schedule.csv

Exit codes:
  0  schedule generated successfully
  1  input file missing/unreadable
  2  input has malformed rows
  3  computed schedule exceeds per-day envelope (caller must spill to queue)
"""

from __future__ import annotations
import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--rate-per-minute", type=float, default=15.0)
    ap.add_argument("--target-window-seconds", type=float, default=120.0)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--start-at", help="ISO timestamp to start the schedule (default: now)")
    ap.add_argument(
        "--max-batch", type=int, default=200, help="if N > max-batch, exit 3 (caller should spill to queue)"
    )
    args = ap.parse_args()

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 1

    try:
        with args.input.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"could not read input: {e}", file=sys.stderr)
        return 1

    flattened: list[tuple[str]] = []  # (endpoint,) per request
    for i, row in enumerate(rows):
        try:
            count = int(row.get("request_count") or 1)
            endpoint = row.get("endpoint") or "default"
        except Exception as e:
            print(f"row {i + 2}: bad value: {e}", file=sys.stderr)
            return 2
        for _ in range(count):
            flattened.append((endpoint,))

    n = len(flattened)
    if n == 0:
        print("input contained zero requests", file=sys.stderr)
        return 2

    if n > args.max_batch:
        print(
            f"batch size {n} exceeds --max-batch {args.max_batch}; spill excess to a durable queue",
            file=sys.stderr,
        )
        return 3

    ideal_delay = args.target_window_seconds / n
    rate_delay = 60.0 / args.rate_per_minute
    delay = max(ideal_delay, rate_delay)

    start = parse_iso(args.start_at) if args.start_at else datetime.now(timezone.utc)
    with args.output.open("w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["scheduled_at_iso", "endpoint", "request_index"])
        for i, (endpoint,) in enumerate(flattened):
            t = start + timedelta(seconds=delay * i)
            w.writerow([t.isoformat().replace("+00:00", "Z"), endpoint, i])

    total_window = delay * (n - 1)
    print(
        f"smoothed {n} requests over {total_window:.1f}s "
        f"(delay={delay:.2f}s; ideal={ideal_delay:.2f}s; rate_bound={rate_delay:.2f}s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
