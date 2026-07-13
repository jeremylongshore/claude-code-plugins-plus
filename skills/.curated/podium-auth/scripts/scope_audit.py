#!/usr/bin/env python3
"""scope_audit.py — compare a Podium OAuth token's granted scopes against the required set.

Usage:
  scope_audit.py --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \\
                 --required conversations.read,conversations.write,contacts.read,contacts.write

Exit codes:
  0  all required scopes are granted
  1  one or more required scopes are missing (drift detected)
  2  could not read the refresh-token record or it has no scopes_granted field
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    ap.add_argument("--required", required=True, help="comma-separated scope strings")
    args = ap.parse_args()

    try:
        record = json.loads(args.refresh_token_file.read_text())
    except Exception as e:
        print(f"could not read {args.refresh_token_file}: {e}", file=sys.stderr)
        return 2

    granted = set(record.get("scopes_granted") or [])
    if not granted:
        print("record has no scopes_granted — run token_refresh.py first", file=sys.stderr)
        return 2

    required = {s.strip() for s in args.required.split(",") if s.strip()}
    missing = sorted(required - granted)
    extra = sorted(granted - required)

    print(
        json.dumps(
            {
                "required_count": len(required),
                "granted_count": len(granted),
                "missing": missing,
                "extra": extra,
            },
            indent=2,
        )
    )

    if missing:
        print(f"ERR_AUTH_007 scope_drift — missing: {missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
