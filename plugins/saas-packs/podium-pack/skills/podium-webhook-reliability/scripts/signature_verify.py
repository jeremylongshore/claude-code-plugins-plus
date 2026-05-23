#!/usr/bin/env python3
"""signature_verify.py — verify a captured Podium webhook payload against a signing secret.

Use this for incident forensics: was a captured POST genuine, or forged?
Reads the body from a file (preserving raw bytes) and parses the signature header
into (t, v1), then runs the same HMAC-SHA256 + constant-time compare the receiver uses.

Usage:
  signature_verify.py \\
    --body-file /tmp/captured_webhook_body.json \\
    --signature-header "t=<unix_ts>,v1=<hex_hmac>" \\
    --secret-env PODIUM_WEBHOOK_SECRET \\
    [--replay-window-seconds 300] \\
    [--ignore-replay-window]

Exit codes:
  0  signature valid AND within replay window
  1  signature mismatch
  2  signature valid BUT replay window exceeded
  3  configuration error (missing env, missing file, malformed header)
"""

from __future__ import annotations
import argparse
import hashlib
import hmac
import os
import sys
import time
from pathlib import Path


def parse_header(header_value: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in header_value.split(","):
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--body-file", required=True, type=Path)
    ap.add_argument("--signature-header", required=True, help='Full header value, e.g. "t=<unix_ts>,v1=<hex_hmac>"')
    ap.add_argument("--secret-env", required=True, help="Env var name holding the webhook signing secret")
    ap.add_argument("--replay-window-seconds", type=int, default=300)
    ap.add_argument(
        "--ignore-replay-window", action="store_true", help="Verify signature only; do not check the timestamp window"
    )
    args = ap.parse_args()

    secret = os.environ.get(args.secret_env)
    if not secret:
        print(f"ERR_WHK_CFG missing env var {args.secret_env}", file=sys.stderr)
        return 3

    if not args.body_file.exists():
        print(f"ERR_WHK_CFG body file not found: {args.body_file}", file=sys.stderr)
        return 3

    raw = args.body_file.read_bytes()
    parts = parse_header(args.signature_header)
    ts, sig = parts.get("t"), parts.get("v1")
    if not ts or not sig:
        print(f"ERR_WHK_012 signature_format_invalid — got keys: {list(parts)}", file=sys.stderr)
        return 3

    signed_payload = f"{ts}.".encode("utf-8") + raw
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, sig):
        print("ERR_WHK_002 signature_mismatch", file=sys.stderr)
        print(f"  expected: {expected[:8]}... ({len(expected)} hex chars)", file=sys.stderr)
        print(f"  received: {sig[:8]}... ({len(sig)} hex chars)", file=sys.stderr)
        return 1

    if not args.ignore_replay_window:
        try:
            ts_int = int(ts)
        except ValueError:
            print(f"ERR_WHK_012 timestamp not an integer: {ts!r}", file=sys.stderr)
            return 3
        skew = abs(time.time() - ts_int)
        if skew > args.replay_window_seconds:
            print(
                f"ERR_WHK_003 replay_window_exceeded — skew={skew:.0f}s > {args.replay_window_seconds}s",
                file=sys.stderr,
            )
            return 2

    print("ok: signature valid and within window", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
