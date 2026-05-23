#!/usr/bin/env python3
"""attachment_downloader.py — parallel attachment download with refresh-on-403.

Reads a JSONL export (gzip-compressed), extracts attachment references from each
record, and downloads them in parallel. On 403 (pre-signed URL expired), fetches
a fresh signed URL via GET /v4/attachments/{id} and retries exactly once.

Usage:
  attachment_downloader.py \\
    --input ./exports/conversations.jsonl.gz \\
    --out-dir ./exports/attachments \\
    [--concurrency 8] \\
    [--refresh-on-403] \\
    --client-id-env PODIUM_CLIENT_ID \\
    --client-secret-env PODIUM_CLIENT_SECRET \\
    --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"

Exit codes:
  0  all attachments downloaded (or attempted with a written failure report)
  1  configuration error
  2  too many failures (>50% of attachments failed after refresh)
"""

from __future__ import annotations
import argparse
import gzip
import json
import os
import sys
import concurrent.futures
from pathlib import Path
from urllib.parse import urlencode
import urllib.request
import urllib.error

API_BASE = "https://api.podium.com"
TOKEN_URL = "https://accounts.podium.com/oauth/token"


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    body = urlencode(
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


def refresh_signed_url(token: str, attachment_id: str) -> str | None:
    req = urllib.request.Request(
        f"{API_BASE}/v4/attachments/{attachment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("url")
    except urllib.error.HTTPError:
        return None


def download_one(token: str, att: dict, out_dir: Path, refresh_on_403: bool, timeout: float = 60.0) -> dict:
    att_id = att["id"]
    url = att.get("url")
    ext = att.get("ext", "")
    dest = out_dir / f"{att_id}{ext}"

    if dest.exists():
        return {"id": att_id, "status": "skipped_exists"}

    def _fetch(u: str) -> tuple[int, bytes | None]:
        try:
            with urllib.request.urlopen(u, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, None
        except urllib.error.URLError:
            return 0, None

    status, data = _fetch(url)
    refreshed = False
    if status == 403 and refresh_on_403:
        fresh = refresh_signed_url(token, att_id)
        if fresh:
            refreshed = True
            status, data = _fetch(fresh)

    if status == 200 and data is not None:
        # Atomic write: temp + rename
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        tmp.rename(dest)
        return {"id": att_id, "status": "ok", "refreshed": refreshed, "bytes": len(data)}

    if status == 403:
        return {"id": att_id, "status": "ERR_EXPORT_003_url_expired_repeat", "refreshed": refreshed}
    if status == 0:
        return {"id": att_id, "status": "ERR_EXPORT_010_partial_or_network", "refreshed": refreshed}
    return {"id": att_id, "status": f"http_{status}", "refreshed": refreshed}


def iter_attachments(jsonl_path: Path):
    """Yield attachment dicts from a JSONL export. Handles common shapes."""
    open_fn = gzip.open if str(jsonl_path).endswith(".gz") else open
    with open_fn(jsonl_path, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            for att in row.get("attachments", []) or []:
                if isinstance(att, dict) and att.get("id") and att.get("url"):
                    yield att
            for msg in row.get("messages", []) or []:
                for att in msg.get("attachments") or []:
                    if isinstance(att, dict) and att.get("id") and att.get("url"):
                        yield att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--refresh-on-403", action="store_true", default=True)
    ap.add_argument("--client-id-env", default="PODIUM_CLIENT_ID")
    ap.add_argument("--client-secret-env", default="PODIUM_CLIENT_SECRET")
    ap.add_argument("--refresh-token-file", required=True, type=Path)
    args = ap.parse_args()

    cid = os.environ.get(args.client_id_env)
    csec = os.environ.get(args.client_secret_env)
    if not cid or not csec:
        print("missing env credentials", file=sys.stderr)
        return 1

    try:
        rec = json.loads(args.refresh_token_file.read_text())
        token = get_access_token(cid, csec, rec["refresh_token"])
    except Exception as e:
        print(f"auth setup failed: {e}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    atts = list(iter_attachments(args.input))
    if not atts:
        print(json.dumps({"attachments_total": 0, "note": "no attachments in export"}))
        return 0

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(download_one, token, a, args.out_dir, args.refresh_on_403) for a in atts]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped_exists"]
    refreshed = [r for r in results if r.get("refreshed")]
    failed = [r for r in results if r["status"] not in ("ok", "skipped_exists")]

    summary = {
        "attachments_total": len(atts),
        "downloaded_ok": len(ok),
        "skipped_already_exists": len(skipped),
        "refreshed_signed_url": len(refreshed),
        "failed_after_refresh": len(failed),
        "failed_ids": [r["id"] for r in failed][:50],  # cap report size
    }
    print(json.dumps(summary, indent=2))

    if failed and len(failed) > len(atts) // 2:
        print("more than 50% of attachments failed — investigate before re-running", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
