#!/usr/bin/env python3
"""onboard_location.py — idempotently onboard a new Podium location into the
credentials map. Records credentials, verifies ownership, adds to the map atomically,
emits an onboarding audit record.

Workflow:
  1. Detect if location_uid is already in the map — if so, exit 0 with skipped_existing.
  2. Write the new credential entry to a temp file.
  3. Refresh an access token using the provided client_id/client_secret/refresh_token.
  4. Call GET /v4/locations and confirm the new location_uid is in scope.
  5. On full success: rename temp → live credentials map (atomic), emit audit.
  6. On any failure: temp file is unlinked; map is unchanged.

Usage:
  onboard_location.py \\
    --location-uid {your-new-location-uid} \\
    --org-slug acme-rv-sydney \\
    --client-id-env PODIUM_CLIENT_ID \\
    --client-secret-env PODIUM_CLIENT_SECRET \\
    --refresh-token-file ./secrets/new-store-refresh.json \\
    --credentials-file ./config/locations.json \\
    [--audit-log ./audit-log/onboarding.jsonl] \\
    [--rate-limit-capacity 30] \\
    [--rate-limit-refill-per-second 5]

Exit codes:
  0  onboarded successfully OR location was already onboarded (idempotent)
  1  verification failed — location_uid not in /v4/locations scope
  2  configuration error (missing env, unreadable file, malformed map)
  3  Podium-side error during onboarding (auth or verification 5xx)
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://accounts.podium.com/oauth/token"
LOCATIONS_URL = "https://api.podium.com/v4/locations"


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> tuple[int, dict]:
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
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def fetch_locations(token: str) -> tuple[int, list[str]]:
    req = urllib.request.Request(
        LOCATIONS_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            return resp.status, [loc["uid"] for loc in body.get("locations", [])]
    except urllib.error.HTTPError as e:
        return e.code, []
    except urllib.error.URLError:
        return 0, []


def atomic_write_map(path: Path, current: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".locations.")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(current, f, indent=2)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def emit_onboarding_audit(path: str | None, record: dict) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--location-uid", required=True)
    ap.add_argument("--org-slug", required=True)
    ap.add_argument("--client-id-env", required=True)
    ap.add_argument("--client-secret-env", required=True)
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    ap.add_argument("--credentials-file", required=True, type=Path)
    ap.add_argument("--audit-log", default=None)
    ap.add_argument("--rate-limit-capacity", type=int, default=30)
    ap.add_argument("--rate-limit-refill-per-second", type=float, default=5.0)
    args = ap.parse_args()

    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    if not cid or not csec:
        print(f"missing env {args.client_id_env} or {args.client_secret_env}", file=sys.stderr)
        return 2

    # Load current map (or initialize empty).
    if args.credentials_file.exists():
        try:
            current = json.loads(args.credentials_file.read_text())
        except Exception as e:
            print(f"ERR_LOC_008 could not parse credentials map: {e}", file=sys.stderr)
            return 2
    else:
        current = {}

    # Idempotence — already onboarded?
    if args.location_uid in current:
        summary = {
            "location_uid": args.location_uid,
            "status": "skipped_existing",
        }
        emit_onboarding_audit(args.audit_log, {**summary, "ts": time.time()})
        print(json.dumps(summary, indent=2))
        return 0

    # Read refresh token.
    try:
        refresh_record = json.loads(args.refresh_token_file.read_text())
    except Exception as e:
        print(f"could not read refresh token file: {e}", file=sys.stderr)
        return 2

    # Refresh + verify in scope.
    status, body = refresh_access_token(cid, csec, refresh_record["refresh_token"])
    if status != 200:
        print(f"ERR_LOC_003 auth refresh failed status={status} body={body}", file=sys.stderr)
        return 3

    s2, scope = fetch_locations(body["access_token"])
    if s2 != 200:
        print(f"ERR_LOC_003 /v4/locations failed status={s2}", file=sys.stderr)
        return 3
    if args.location_uid not in scope:
        print(
            f"ERR_LOC_002 location_not_in_scope — uid={args.location_uid} "
            f"not in scope of {len(scope)} locations the credential sees.",
            file=sys.stderr,
        )
        return 1

    # Commit to the map atomically.
    current[args.location_uid] = {
        "org_slug": args.org_slug,
        "client_id": cid,
        "client_secret": csec,
        "refresh_token_file": str(args.refresh_token_file),
        "rate_limit": {
            "capacity": args.rate_limit_capacity,
            "refill_per_second": args.rate_limit_refill_per_second,
        },
    }
    try:
        atomic_write_map(args.credentials_file, current)
    except OSError as e:
        print(f"ERR_LOC_006 credential_persistence_failure: {e}", file=sys.stderr)
        return 2

    summary = {
        "location_uid": args.location_uid,
        "org_slug": args.org_slug,
        "status": "onboarded",
        "scope_size": len(scope),
    }
    emit_onboarding_audit(args.audit_log, {**summary, "ts": time.time()})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
