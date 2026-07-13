#!/usr/bin/env python3
"""verify_creds.py — health-check a Podium credential pair without triggering a refresh.

Usage:
  verify_creds.py --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \\
                  [--client-id-env PODIUM_CLIENT_ID] \\
                  [--client-secret-env PODIUM_CLIENT_SECRET]

Strategy:
  1. If a recent access token is available (e.g. in the refresh-token record), try GET /v4/me.
  2. Otherwise, do a single refresh and immediately call /v4/me.

Exit codes:
  0  credential live — /v4/me returned 200
  1  /v4/me returned 401 — token rejected
  2  endpoint reachable but ambiguous (5xx, timeout) — retry later
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

ME_URL = "https://api.podium.com/v4/me"
TOKEN_URL = "https://accounts.podium.com/oauth/token"


def refresh(client_id: str, client_secret: str, refresh_token: str, timeout: float = 10.0) -> str | None:
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError:
        return None


def get_me(token: str, timeout: float = 5.0) -> int:
    req = urllib.request.Request(ME_URL, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    ap.add_argument("--client-id-env", default="PODIUM_CLIENT_ID")
    ap.add_argument("--client-secret-env", default="PODIUM_CLIENT_SECRET")
    args = ap.parse_args()

    record = json.loads(args.refresh_token_file.read_text())
    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    if not cid or not csec:
        print("missing env credentials", file=sys.stderr)
        return 2

    token = refresh(cid, csec, record["refresh_token"])
    if token is None:
        print("refresh failed — credential cannot be verified", file=sys.stderr)
        return 1

    status = get_me(token)
    if status == 200:
        print("ok", file=sys.stderr)
        return 0
    if status == 401:
        print("rejected (401)", file=sys.stderr)
        return 1
    print(f"ambiguous (status={status})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
