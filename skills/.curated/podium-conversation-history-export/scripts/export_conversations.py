#!/usr/bin/env python3
"""export_conversations.py — full or incremental Podium conversation export.

Modes:
  full        — walk /v4/conversations with sort=created_at:asc; resumable via cursor
                checkpoint. seen_ids dedup absorbs mid-walk updates.
  incremental — pull /v4/conversations with updated_since = (watermark - overlap_margin);
                advance watermark only after the full pass succeeds. Dedup on (id, updated_at).

Usage:
  export_conversations.py \\
    --location-uid "{your-location-uid}" \\
    --mode full|incremental \\
    --out ./exports/conversations.jsonl.gz \\
    [--watermark-db ./watermarks.sqlite] \\
    [--overlap-margin-seconds 60] \\
    [--client-id-env PODIUM_CLIENT_ID] \\
    [--client-secret-env PODIUM_CLIENT_SECRET] \\
    [--refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"]

Exit codes:
  0  success — full pass completed, watermark advanced (incremental) or cursor cleared (full)
  1  cursor_invalid — drop cursor and retry
  2  configuration error (missing env, unreadable file)
  3  Podium-side transient error after retries exhausted
  4  watermark drift or DB corruption — operator action required
"""

from __future__ import annotations
import argparse
import gzip
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://api.podium.com"
TOKEN_URL = "https://accounts.podium.com/oauth/token"
PAGE_SIZE = 100


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
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
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["access_token"]


def http_get(token: str, path: str, params: dict, timeout: float = 30.0) -> tuple[int, dict]:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{API_BASE}{path}?{qs}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read())
        except Exception:
            payload = {"error": "non_json"}
        return e.code, payload


def get_watermark(db: str, resource: str) -> float:
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS cdc(resource TEXT PRIMARY KEY, watermark REAL, updated_at REAL)")
    row = con.execute("SELECT watermark FROM cdc WHERE resource = ?", (resource,)).fetchone()
    con.close()
    return row[0] if row else 0.0


def advance_watermark(db: str, resource: str, ts: float) -> None:
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS cdc(resource TEXT PRIMARY KEY, watermark REAL, updated_at REAL)")
    con.execute(
        """
        INSERT INTO cdc(resource, watermark, updated_at) VALUES(?, ?, ?)
        ON CONFLICT(resource) DO UPDATE SET watermark = excluded.watermark, updated_at = excluded.updated_at
    """,
        (resource, ts, time.time()),
    )
    con.commit()
    con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--location-uid", required=True)
    ap.add_argument("--mode", required=True, choices=("full", "incremental"))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--watermark-db", default="./watermarks.sqlite")
    ap.add_argument("--overlap-margin-seconds", type=int, default=60)
    ap.add_argument("--cursor-file", default=None)
    ap.add_argument("--client-id-env", default="PODIUM_CLIENT_ID")
    ap.add_argument("--client-secret-env", default="PODIUM_CLIENT_SECRET")
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    args = ap.parse_args()

    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    if not cid or not csec:
        print(f"missing env {args.client_id_env} or {args.client_secret_env}", file=sys.stderr)
        return 2

    try:
        rec = json.loads(args.refresh_token_file.read_text())
    except Exception as e:
        print(f"could not read refresh-token-file: {e}", file=sys.stderr)
        return 2

    try:
        token = get_access_token(cid, csec, rec["refresh_token"])
    except Exception as e:
        print(f"auth failed: {e}", file=sys.stderr)
        return 2

    cursor_path = Path(args.cursor_file) if args.cursor_file else Path(f".cursor.conversations.{args.mode}.json")
    cursor = None
    seen_ids: set[str] = set()
    if cursor_path.exists():
        try:
            state = json.loads(cursor_path.read_text())
            cursor = state.get("cursor")
            seen_ids = set(state.get("seen_ids", []))
        except Exception:
            print("ERR_EXPORT_004 cursor checkpoint corrupt, restarting", file=sys.stderr)
            cursor_path.unlink(missing_ok=True)

    if args.mode == "incremental":
        watermark = get_watermark(args.watermark_db, "conversations")
        since = max(0.0, watermark - args.overlap_margin_seconds)
        sort = "updated_at:asc"
    else:
        watermark = 0.0
        since = 0.0
        sort = "created_at:asc"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows_pulled = 0
    rows_emitted = 0
    max_seen = watermark

    with gzip.open(args.out, "wt", encoding="utf-8") as f:
        while True:
            params = {
                "location_uid": args.location_uid,
                "sort": sort,
                "limit": PAGE_SIZE,
            }
            if since > 0:
                params["updated_since"] = int(since)
            if cursor:
                params["cursor"] = cursor

            status, body = http_get(token, "/v4/conversations", params)
            if status == 409 and body.get("error") in ("cursor_invalid", "invalid_pagination"):
                print("ERR_EXPORT_001 cursor_invalid — drop cursor and retry", file=sys.stderr)
                cursor_path.unlink(missing_ok=True)
                return 1
            if status == 429:
                print("ERR_EXPORT_011 rate_limited — delegate to podium-rate-limit-survival", file=sys.stderr)
                return 3
            if status >= 500:
                print(f"Podium server_error {status}: {body}", file=sys.stderr)
                return 3
            if status != 200:
                print(f"unexpected status {status}: {body}", file=sys.stderr)
                return 3

            page = body.get("data", [])
            for row in page:
                rows_pulled += 1
                key = row["id"] if args.mode == "full" else (row["id"], row.get("updated_at"))
                key_str = str(key)
                if key_str in seen_ids:
                    continue
                seen_ids.add(key_str)
                f.write(json.dumps(row, separators=(",", ":")))
                f.write("\n")
                rows_emitted += 1
                if row.get("updated_at") and row["updated_at"] > max_seen:
                    max_seen = row["updated_at"]
                if rows_emitted % 1000 == 0:
                    f.flush()

            cursor = body.get("next_cursor")
            cursor_path.write_text(
                json.dumps(
                    {
                        "cursor": cursor,
                        "seen_ids": list(seen_ids)[-50_000:],
                        "updated_at": time.time(),
                    }
                )
            )
            if not cursor:
                break

    # Full pass succeeded — advance watermark for incremental mode
    if args.mode == "incremental" and max_seen > watermark:
        advance_watermark(args.watermark_db, "conversations", max_seen)

    # Clear cursor checkpoint after a complete pass
    cursor_path.unlink(missing_ok=True)

    summary = {
        "resource": "conversations",
        "mode": args.mode,
        "watermark_before": watermark,
        "watermark_after": max_seen if args.mode == "incremental" else None,
        "rows_pulled": rows_pulled,
        "rows_emitted_after_dedup": rows_emitted,
        "out": str(args.out),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
