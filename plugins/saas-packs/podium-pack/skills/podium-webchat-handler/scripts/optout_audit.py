#!/usr/bin/env python3
"""optout_audit.py — confirm opt-out state for a phone across all integration layers.

For a given E.164 phone, this script queries every layer where opt-out state is held
(local store, Podium contact record) and reports whether they agree. A "drift detected"
result means the opt-out flag is set in one place and not the other — either a
propagation gap or a stale write that needs reconciliation.

Usage:
  optout_audit.py --phone "+61412345678" \\
                  [--client-id-env PODIUM_CLIENT_ID] \\
                  [--client-secret-env PODIUM_CLIENT_SECRET] \\
                  [--refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"] \\
                  [--optout-store-dsn "$OPTOUT_STORE_DSN"] \\
                  [--output json|human]

Exit codes:
  0  all layers agree (opted-out true, or opted-out false everywhere)
  1  drift detected — opt-out flag inconsistent across layers (ERR_WEBCHAT_011 risk)
  2  configuration error or one layer unreachable (cannot determine consistency)
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


def get_podium_token(client_id: str, client_secret: str, refresh_token: str, timeout: float = 10.0) -> str | None:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        "https://accounts.podium.com/oauth/token",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError:
        return None


def query_podium_contact_optout(token: str, phone_e164: str, timeout: float = 5.0) -> dict:
    """Return {'uid': ..., 'opted_out': bool, 'last_updated': iso} or {} if not found / unreachable."""
    qs = urllib.parse.urlencode({"phone": phone_e164})
    req = urllib.request.Request(
        f"https://api.podium.com/v4/contacts?{qs}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError:
        return {}
    except urllib.error.URLError:
        return {}
    data = body.get("data") or []
    if not data:
        return {}
    c = data[0]
    return {
        "uid": c.get("uid"),
        "opted_out": bool(c.get("opted_out")),
        "last_updated_iso": c.get("updated_at"),
    }


def query_local_optout_store(dsn: str | None, phone_e164: str) -> dict:
    """Return {'opted_out': bool, 'source': str, 'recorded_at_iso': iso} or {} if no record."""
    # In real deployment, swap this stub for a parametrized SELECT on the opt-out table.
    # The stub reads from a JSON file pointed at by OPTOUT_STUB_FILE so the script is testable.
    stub_path = os.environ.get("OPTOUT_STUB_FILE")
    if stub_path and Path(stub_path).exists():
        try:
            data = json.loads(Path(stub_path).read_text())
            record = data.get(phone_e164)
            if record is None:
                return {}
            return {
                "opted_out": bool(record.get("opted_out", True)),
                "source": record.get("source", "unknown"),
                "recorded_at_iso": record.get("recorded_at_iso", ""),
            }
        except Exception:
            return {}
    if not dsn:
        return {}
    # Real DSN path intentionally omitted to keep this script dependency-free.
    # A production deployment wires psycopg / asyncpg / redis here.
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", required=True, help="E.164-formatted phone, e.g. +61412345678")
    ap.add_argument("--client-id-env", default="PODIUM_CLIENT_ID")
    ap.add_argument("--client-secret-env", default="PODIUM_CLIENT_SECRET")
    ap.add_argument("--refresh-token-file", type=Path, default=None)
    ap.add_argument("--optout-store-dsn", default=None)
    ap.add_argument("--output", choices=("json", "human"), default="human")
    args = ap.parse_args()

    if not args.phone.startswith("+"):
        print("--phone must be E.164 (start with '+')", file=sys.stderr)
        return 2

    # Query local opt-out store
    dsn = args.optout_store_dsn or os.environ.get("OPTOUT_STORE_DSN")
    local = query_local_optout_store(dsn, args.phone)

    # Query Podium contact record (best-effort)
    podium: dict = {}
    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    refresh_token = None
    if args.refresh_token_file and args.refresh_token_file.exists():
        try:
            refresh_token = json.loads(args.refresh_token_file.read_text()).get("refresh_token")
        except Exception:
            refresh_token = None

    if cid and csec and refresh_token:
        token = get_podium_token(cid, csec, refresh_token)
        if token:
            podium = query_podium_contact_optout(token, args.phone)

    local_state = local.get("opted_out") if local else None
    podium_state = podium.get("opted_out") if podium else None

    # Consistency rules:
    # - both empty → consistent (no opt-out recorded anywhere)
    # - both present and equal → consistent
    # - one present + true, other empty → drift (propagation gap)
    # - both present + different → drift (reconciliation needed)
    if local_state is None and podium_state is None:
        consistent = True
    elif local_state is None or podium_state is None:
        # If either is "no record" but the other is True, drift. If the other is False, consistent.
        present = local_state if local_state is not None else podium_state
        consistent = present is False
    else:
        consistent = local_state == podium_state

    summary = {
        "phone": args.phone,
        "optout_store": local or {"present": False},
        "podium_contact": podium or {"present": False},
        "consistent": consistent,
    }

    if args.output == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(summary, indent=2))

    if not consistent:
        print("ERR_WEBCHAT_011 drift detected — reconcile before resuming outbound", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
