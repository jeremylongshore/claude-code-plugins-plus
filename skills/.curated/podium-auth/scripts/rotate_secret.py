#!/usr/bin/env python3
"""rotate_secret.py — dual-credential rotation orchestrator for the Podium OAuth client secret.

Workflow:
  1. Refresh an access token using the NEW client_secret.
  2. Call GET /v4/me with the new token N consecutive times — all must succeed.
  3. Sleep overlap_window_seconds to let in-flight handlers drain on the old secret.
  4. POST /oauth/revoke against the OLD client_secret.

Usage:
  rotate_secret.py \\
    --old-secret-env PODIUM_CLIENT_SECRET_V1 \\
    --new-secret-env PODIUM_CLIENT_SECRET_V2 \\
    --client-id-env  PODIUM_CLIENT_ID \\
    --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \\
    --health-check-passes 3 \\
    --overlap-window-seconds 900

Exit codes:
  0  rotation complete — old secret revoked
  1  health check failed against new secret — rotation ABORTED (old secret retained)
  2  configuration error (missing env, unreadable file)
  3  Podium-side error during the rotation flow
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

TOKEN_URL = "https://accounts.podium.com/oauth/token"
ME_URL = "https://api.podium.com/v4/me"
REVOKE_URL = "https://accounts.podium.com/oauth/revoke"


def refresh(client_id: str, client_secret: str, refresh_token: str) -> tuple[int, dict]:
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
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read())
        except Exception:
            payload = {"error": "non_json"}
        return e.code, payload


def call_me(token: str) -> int:
    req = urllib.request.Request(ME_URL, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError:
        return 0


def revoke(client_id: str, client_secret: str, token: str) -> int:
    body = urllib.parse.urlencode(
        {
            "token": token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        REVOKE_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old-secret-env", required=True)
    ap.add_argument("--new-secret-env", required=True)
    ap.add_argument("--client-id-env", required=True)
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    ap.add_argument("--health-check-passes", type=int, default=3)
    ap.add_argument("--overlap-window-seconds", type=int, default=900)
    args = ap.parse_args()

    cid = os.environ.get(args.client_id_env)
    old_sec = os.environ.get(args.old_secret_env)
    new_sec = os.environ.get(args.new_secret_env)
    if not all([cid, old_sec, new_sec]):
        print("ERR_AUTH_002 missing one of client_id, old_secret, new_secret in env", file=sys.stderr)
        return 2

    try:
        record = json.loads(args.refresh_token_file.read_text())
    except Exception as e:
        print(f"could not read refresh-token-file: {e}", file=sys.stderr)
        return 2

    # Step 1: refresh using the NEW secret
    print("[1/4] refresh using new secret", file=sys.stderr)
    status, body = refresh(cid, new_sec, record["refresh_token"])
    if status != 200:
        print(f"ERR_AUTH_013 refresh with new secret failed: {status} {body}", file=sys.stderr)
        return 3
    token = body["access_token"]

    # Step 2: N consecutive /v4/me successes
    print(f"[2/4] {args.health_check_passes} consecutive /v4/me calls", file=sys.stderr)
    for i in range(args.health_check_passes):
        s = call_me(token)
        if s != 200:
            print(f"ERR_AUTH_013 /v4/me pass {i + 1} failed: status={s}", file=sys.stderr)
            print("ROTATION ABORTED — old secret retained, NOT revoking.", file=sys.stderr)
            return 1
        print(f"  pass {i + 1}/{args.health_check_passes}: ok", file=sys.stderr)

    # Step 3: overlap window
    print(f"[3/4] sleeping {args.overlap_window_seconds}s for in-flight handlers to drain", file=sys.stderr)
    time.sleep(args.overlap_window_seconds)

    # Step 4: revoke OLD secret
    print("[4/4] revoking old secret", file=sys.stderr)
    s = revoke(cid, old_sec, record["refresh_token"])
    if s not in (200, 204):
        print(
            f"warn: revoke returned {s} — old credential may still be live; verify in Podium console", file=sys.stderr
        )
        return 3
    print("rotation complete", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
