#!/usr/bin/env python3
"""retry_after_parse.py — parse a Retry-After header to absolute UTC wakeup time.

Accepts both RFC 7231 forms:
  - integer seconds:  Retry-After: 30
  - HTTP-date:        Retry-After: Wed, 09 May 2026 17:05:00 GMT

Useful during on-call: paste the Retry-After header from a paging alert and
get the absolute UTC wakeup time so you know whether to wait or escalate.

Usage:
  retry_after_parse.py --header "30"
  retry_after_parse.py --header "Wed, 09 May 2026 17:05:00 GMT"
  retry_after_parse.py --header "$(curl -sI ... | grep -i retry-after | cut -d: -f2-)"
  retry_after_parse.py --header "$VAL" --cap-seconds 120

Exit codes:
  0  parsed successfully (within cap)
  1  parsed successfully but exceeded cap (capped value used in output)
  2  malformed header — fell back to default (60s)
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_retry_after(header_value: str) -> tuple[float, str]:
    """Return (wait_seconds, parse_method). parse_method ∈ {int, http_date, default}."""
    header_value = header_value.strip()
    # Strip a leading "retry-after:" if the caller pasted the whole header line
    if ":" in header_value and header_value.lower().split(":", 1)[0].strip() == "retry-after":
        header_value = header_value.split(":", 1)[1].strip()

    # Integer seconds first — most common form Podium returns
    try:
        seconds = int(header_value)
        return (max(0.0, float(seconds)), "int")
    except ValueError:
        pass

    # HTTP-date form — RFC 7231
    try:
        retry_at = parsedate_to_datetime(header_value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        delta = (retry_at - datetime.now(timezone.utc)).total_seconds()
        return (max(0.0, delta), "http_date")
    except (TypeError, ValueError):
        pass

    # Fallback — never crash on malformed input
    return (60.0, "default")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--header", required=True, help="Retry-After header value")
    ap.add_argument("--cap-seconds", type=float, default=120.0, help="cap the wait at this many seconds (default 120)")
    ap.add_argument(
        "--default-on-malformed", type=float, default=60.0, help="fallback wait if neither parser succeeds (default 60)"
    )
    args = ap.parse_args()

    wait_s, method = parse_retry_after(args.header)
    if method == "default":
        wait_s = args.default_on_malformed

    capped = False
    if wait_s > args.cap_seconds:
        wait_s = args.cap_seconds
        capped = True

    wakeup = datetime.now(timezone.utc).timestamp() + wait_s
    wakeup_iso = datetime.fromtimestamp(wakeup, tz=timezone.utc).isoformat()

    print(
        json.dumps(
            {
                "wait_seconds": round(wait_s, 2),
                "parse_method": method,
                "capped_to_max": capped,
                "absolute_wakeup_utc": wakeup_iso,
            }
        )
    )

    if method == "default":
        return 2
    if capped:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
