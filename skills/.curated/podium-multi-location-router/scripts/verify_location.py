#!/usr/bin/env python3
"""verify_location.py — confirm a location_uid is reachable with the credential
stored in the credentials map. Pre-flight check that prevents silent wrong-location
writes.

Usage:
  verify_location.py --location-uid {your-location-uid} \\
                     --credentials-file ./config/locations.json \\
                     [--output json|human]

Exit codes:
  0  in scope — the credential's token sees this location_uid
  1  not in scope — pre-flight prevented a silent 403 / wrong-org write
  2  configuration error (map missing, malformed, or credential unreadable)
  3  Podium-side error (5xx, timeout)
"""

from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://accounts.podium.com/oauth/token"
LOCATIONS_URL = "https://api.podium.com/v4/locations"


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str | None:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError:
        return None
    except urllib.error.URLError:
        return None


def fetch_locations(token: str) -> tuple[int, list[str]]:
    req = urllib.request.Request(
        LOCATIONS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            uids = [loc["uid"] for loc in body.get("locations", [])]
            return resp.status, uids
    except urllib.error.HTTPError as e:
        return e.code, []
    except urllib.error.URLError:
        return 0, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--location-uid", required=True)
    ap.add_argument("--credentials-file", required=True, type=Path)
    ap.add_argument("--output", choices=("json", "human"), default="human")
    args = ap.parse_args()

    try:
        creds_map = json.loads(args.credentials_file.read_text())
    except Exception as e:
        print(f"ERR_LOC_008 could not read {args.credentials_file}: {e}", file=sys.stderr)
        return 2

    entry = creds_map.get(args.location_uid)
    if not entry:
        print(f"ERR_LOC_001 unknown_location_uid: {args.location_uid} not in map", file=sys.stderr)
        return 2

    try:
        refresh_record = json.loads(Path(entry["refresh_token_file"]).read_text())
    except Exception as e:
        print(f"could not read refresh token file: {e}", file=sys.stderr)
        return 2

    token = refresh_access_token(
        entry["client_id"],
        entry["client_secret"],
        refresh_record["refresh_token"],
    )
    if token is None:
        print("auth refresh failed — credential cannot be verified", file=sys.stderr)
        return 3

    status, scope = fetch_locations(token)
    if status == 0:
        print("ERR_LOC_003 verification_endpoint_unreachable", file=sys.stderr)
        return 3
    if status >= 500:
        print(f"ERR_LOC_003 verification_endpoint_unreachable (status={status})", file=sys.stderr)
        return 3
    if status != 200:
        print(f"unexpected status from /v4/locations: {status}", file=sys.stderr)
        return 3

    in_scope = args.location_uid in scope
    summary = {
        "location_uid": args.location_uid,
        "status": "in_scope" if in_scope else "not_in_scope",
        "scope_size": len(scope),
        "verified_at": time.time() if in_scope else None,
    }
    if not in_scope:
        summary["scope"] = sorted(scope)

    if args.output == "json":
        print(json.dumps(summary, indent=2))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")

    if not in_scope:
        print(
            f"ERR_LOC_002 location_not_in_scope — uid={args.location_uid} not in scope.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
