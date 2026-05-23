#!/usr/bin/env python3
"""find_duplicates.py — scan a Podium location's contacts and emit duplicate-cluster proposals.

Usage:
  find_duplicates.py \\
    --location-uid loc_abc123 \\
    --db ./podium-dedup.sqlite \\
    --token-env PODIUM_ACCESS_TOKEN \\
    [--region AU] \\
    [--auto-merge-threshold 0.80] \\
    [--output json|ndjson]

The script:
  1. Pages through GET /v4/contacts?location_uid=... — populates the SQLite natural-key index.
  2. Queries the index for clusters (natural_key with 2+ rows).
  3. Computes pairwise confidence per cluster.
  4. Emits each cluster as a JSON object on stdout.

Exit codes:
  0  success — clusters emitted (may be zero clusters if corpus is clean)
  1  upstream Podium error during scan
  2  local SQLite error during index write
  3  missing env var or unsupported argument
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterable

import urllib.request
import urllib.parse
import urllib.error

try:
    from phone_normalize import normalize_phone
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from phone_normalize import normalize_phone


PODIUM_BASE = "https://api.podium.com"
PAGE_SIZE = 100


SCHEMA = """
CREATE TABLE IF NOT EXISTS contact_index (
    contact_uid        TEXT PRIMARY KEY,
    location_uid       TEXT NOT NULL,
    natural_key        TEXT NOT NULL,
    raw_phone          TEXT,
    name               TEXT,
    email              TEXT,
    tags_json          TEXT,
    field_count        INTEGER NOT NULL DEFAULT 0,
    marketing_opt_out  INTEGER NOT NULL DEFAULT 0,
    sms_opt_out        INTEGER NOT NULL DEFAULT 0,
    email_opt_out      INTEGER NOT NULL DEFAULT 0,
    deleted_at_podium  TEXT,
    updated_at_podium  TEXT NOT NULL,
    indexed_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_natural_key ON contact_index(natural_key);
CREATE INDEX IF NOT EXISTS idx_natural_key_per_location ON contact_index(natural_key, location_uid);
"""


def http_get_json(url: str, token: str, timeout: float = 10.0) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": "non_json", "status": e.code}
        return e.code, body


def field_count(c: dict) -> int:
    # Count non-empty fields on the Podium contact payload.
    n = 0
    for k in (
        "name",
        "first_name",
        "last_name",
        "email",
        "address",
        "city",
        "state",
        "postal_code",
        "country",
        "company",
        "notes",
        "birthday",
    ):
        if c.get(k):
            n += 1
    if c.get("tags"):
        n += 1
    if c.get("phone") or c.get("phone_e164"):
        n += 1
    return n


def open_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    db.commit()
    return db


def upsert_contact(db: sqlite3.Connection, location_uid: str, c: dict, region: str) -> bool:
    raw_phone = c.get("phone") or c.get("phone_number") or ""
    norm = normalize_phone(raw_phone, default_region=region)
    if not norm["valid"]:
        return False
    db.execute(
        """INSERT OR REPLACE INTO contact_index
           (contact_uid, location_uid, natural_key, raw_phone, name, email, tags_json,
            field_count, marketing_opt_out, sms_opt_out, email_opt_out,
            deleted_at_podium, updated_at_podium, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            c["uid"],
            location_uid,
            norm["natural_key"],
            raw_phone,
            c.get("name"),
            c.get("email"),
            json.dumps(c.get("tags") or []),
            field_count(c),
            1 if c.get("marketing_opt_out") else 0,
            1 if c.get("sms_opt_out") else 0,
            1 if c.get("email_opt_out") else 0,
            c.get("deleted_at"),
            c.get("updated_at") or "1970-01-01T00:00:00Z",
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        ),
    )
    return True


def scan_location(db: sqlite3.Connection, location_uid: str, token: str, region: str) -> int:
    count = 0
    cursor = None
    while True:
        params = {"location_uid": location_uid, "page_size": PAGE_SIZE}
        if cursor:
            params["cursor"] = cursor
        url = f"{PODIUM_BASE}/v4/contacts?{urllib.parse.urlencode(params)}"
        status, body = http_get_json(url, token)
        if status != 200:
            sys.stderr.write(f"scan: GET {url} -> {status}: {body}\n")
            return -1
        for c in body.get("data") or []:
            if upsert_contact(db, location_uid, c, region):
                count += 1
        cursor = body.get("next_cursor")
        if not cursor:
            break
    db.commit()
    return count


def cluster_confidence(a: dict, b: dict) -> float:
    score = 0.60  # same natural_key by construction
    if a.get("name") and a["name"].strip().lower() == (b.get("name") or "").strip().lower():
        score += 0.20
    if a.get("email") and a["email"].strip().lower() == (b.get("email") or "").strip().lower():
        score += 0.15
    a_tags = set(json.loads(a.get("tags_json") or "[]"))
    b_tags = set(json.loads(b.get("tags_json") or "[]"))
    if a_tags & b_tags:
        score += 0.05
    return round(min(score, 1.0), 4)


def cluster_id_for(uids: list[str]) -> str:
    h = hashlib.sha1("|".join(sorted(uids)).encode()).hexdigest()[:12]
    return f"cl_{h}"


def select_primary(cluster: list[dict]) -> dict:
    return max(
        cluster,
        key=lambda c: (c["field_count"], c["updated_at_podium"], -sum(ord(x) for x in c["contact_uid"])),
    )


def emit_clusters(db: sqlite3.Connection, location_uid: str, threshold: float) -> Iterable[dict]:
    rows = db.execute(
        """SELECT natural_key, COUNT(*) FROM contact_index
           WHERE location_uid = ? AND deleted_at_podium IS NULL
           GROUP BY natural_key HAVING COUNT(*) >= 2""",
        (location_uid,),
    ).fetchall()
    for natural_key, _ in rows:
        members = [
            dict(
                zip(
                    [
                        "contact_uid",
                        "location_uid",
                        "natural_key",
                        "raw_phone",
                        "name",
                        "email",
                        "tags_json",
                        "field_count",
                        "marketing_opt_out",
                        "sms_opt_out",
                        "email_opt_out",
                        "deleted_at_podium",
                        "updated_at_podium",
                        "indexed_at",
                    ],
                    row,
                )
            )
            for row in db.execute(
                """SELECT contact_uid, location_uid, natural_key, raw_phone, name, email,
                          tags_json, field_count, marketing_opt_out, sms_opt_out,
                          email_opt_out, deleted_at_podium, updated_at_podium, indexed_at
                   FROM contact_index
                   WHERE natural_key = ? AND location_uid = ? AND deleted_at_podium IS NULL""",
                (natural_key, location_uid),
            ).fetchall()
        ]
        if len(members) < 2:
            continue
        # Compute lowest pairwise confidence (most conservative).
        worst = 1.0
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                worst = min(worst, cluster_confidence(members[i], members[j]))
        primary = select_primary(members)
        uids = [m["contact_uid"] for m in members]
        yield {
            "cluster_id": cluster_id_for(uids),
            "natural_key": natural_key,
            "confidence": worst,
            "auto_merge": worst >= threshold,
            "suggested_primary_uid": primary["contact_uid"],
            "members": [
                {
                    "contact_uid": m["contact_uid"],
                    "field_count": m["field_count"],
                    "updated_at": m["updated_at_podium"],
                    "marketing_opt_out": bool(m["marketing_opt_out"]),
                    "sms_opt_out": bool(m["sms_opt_out"]),
                    "email_opt_out": bool(m["email_opt_out"]),
                }
                for m in members
            ],
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--location-uid", required=True)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--token-env", required=True)
    ap.add_argument("--region", default="AU")
    ap.add_argument("--auto-merge-threshold", type=float, default=0.80)
    ap.add_argument("--output", choices=("json", "ndjson"), default="ndjson")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        sys.stderr.write(f"missing env var {args.token_env}\n")
        return 3

    db = open_db(args.db)
    try:
        count = scan_location(db, args.location_uid, token, args.region)
    except sqlite3.Error as e:
        sys.stderr.write(f"sqlite error: {e}\n")
        return 2
    if count < 0:
        return 1
    sys.stderr.write(f"indexed {count} contacts in location={args.location_uid}\n")

    clusters = list(emit_clusters(db, args.location_uid, args.auto_merge_threshold))
    if args.output == "json":
        print(json.dumps(clusters))
    else:
        for c in clusters:
            print(json.dumps(c))
    sys.stderr.write(f"emitted {len(clusters)} clusters\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
