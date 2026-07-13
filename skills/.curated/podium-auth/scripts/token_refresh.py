#!/usr/bin/env python3
"""token_refresh.py — manual Podium OAuth refresh with atomic persistence.

Usage:
  token_refresh.py \\
    --client-id-env PODIUM_CLIENT_ID \\
    --client-secret-env PODIUM_CLIENT_SECRET \\
    --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \\
    [--output json|human]

Exit codes:
  0  success — new access token acquired, new refresh token persisted
  1  401 invalid_grant — refresh token dead, user re-auth required
  2  400 invalid_client — credentials mismatch
  3  429 rate_limited — Podium throttled the token endpoint
  4  5xx server_error — Podium-side transient
  5  scope_drift — refresh succeeded but required scope missing
  6  persistence_failure — could not atomically write new refresh token
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import urllib.request
import urllib.parse
import urllib.error

TOKEN_URL = "https://accounts.podium.com/oauth/token"

REQUIRED_SCOPES = {
    "conversations.read",
    "conversations.write",
    "contacts.read",
    "contacts.write",
    "reviews.read",
    "reviews.write",
}


def http_post_form(url: str, data: dict, timeout: float = 10.0) -> tuple[int, dict]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {"error": "non_json_response", "status": e.code}
        return e.code, payload


def atomic_persist(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".podium_refresh.")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client-id-env", required=True)
    ap.add_argument("--client-secret-env", required=True)
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    ap.add_argument("--output", choices=("json", "human"), default="human")
    args = ap.parse_args()

    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    if not cid or not csec:
        print(f"missing env var {args.client_id_env} or {args.client_secret_env}", file=sys.stderr)
        return 2

    record = json.loads(args.refresh_token_file.read_text())
    refresh = record["refresh_token"]

    status, body = http_post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": cid,
            "client_secret": csec,
        },
    )

    if status == 401:
        print("ERR_AUTH_001 invalid_grant — user re-authorization required", file=sys.stderr)
        return 1
    if status == 400 and body.get("error") == "invalid_client":
        print("ERR_AUTH_002 invalid_client — verify client_id/secret pair", file=sys.stderr)
        return 2
    if status == 429:
        print("ERR_AUTH_005 rate_limited on token endpoint", file=sys.stderr)
        return 3
    if status >= 500:
        print(f"Podium server_error {status}: {body}", file=sys.stderr)
        return 4
    if status != 200:
        print(f"unexpected status {status}: {body}", file=sys.stderr)
        return 4

    granted = set((body.get("scope") or "").split(" "))
    missing = REQUIRED_SCOPES - granted
    if missing:
        print(f"ERR_AUTH_007 scope_drift — missing: {sorted(missing)}", file=sys.stderr)
        return 5

    new_record = {
        "refresh_token": body.get("refresh_token", refresh),
        "last_used_at": time.time(),
        "scopes_granted": sorted(granted),
    }
    try:
        atomic_persist(args.refresh_token_file, new_record)
    except OSError as e:
        print(f"ERR_AUTH_006 persistence_failure: {e}", file=sys.stderr)
        return 6

    summary = {
        "status": "ok",
        "access_token_length": len(body["access_token"]),
        "expires_in": body.get("expires_in"),
        "refresh_token_rotated": body.get("refresh_token") not in (None, refresh),
        "scopes_granted": sorted(granted),
    }
    if args.output == "json":
        print(json.dumps(summary))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
