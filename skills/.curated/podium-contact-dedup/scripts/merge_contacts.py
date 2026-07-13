#!/usr/bin/env python3
"""merge_contacts.py — merge a duplicate cluster with opt-out preservation.

Usage:
  merge_contacts.py --cluster-id cl_7f3a... \\
                    --db ./podium-dedup.sqlite \\
                    --token-env PODIUM_ACCESS_TOKEN \\
                    [--dry-run] \\
                    [--resume]

Behavior:
  1. Look up cluster members from the SQLite natural-key index.
  2. Re-fetch each duplicate from Podium; compare updated_at to indexed value.
     A drift aborts the merge (re_index_required).
  3. Compute opt_out_union across all cluster members.
  4. POST /v4/contacts/{primary}/merge {"duplicate_uids": [...]}.
  5. PATCH /v4/contacts/{primary} with the unioned opt-outs.
  6. Append an audit-log.jsonl entry.

--dry-run prints the planned API calls without contacting Podium.
--resume scans merge_state for non-terminal rows and reconciles against Podium.

Exit codes:
  0  merge completed (status=patched) or dry-run completed
  1  upstream Podium error (transient or permanent — see audit-log for detail)
  2  local SQLite error
  3  missing env var, unsupported argument, or cluster not found
  4  updated_at drift detected — cluster marked re_index_required
  5  compliance failure — merge succeeded but opt-out PATCH failed (page compliance!)
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

import urllib.request
import urllib.parse
import urllib.error


PODIUM_BASE = "https://api.podium.com"
SCHEMA_MERGE_STATE = """
CREATE TABLE IF NOT EXISTS merge_state (
    cluster_id        TEXT PRIMARY KEY,
    natural_key       TEXT NOT NULL,
    primary_uid       TEXT NOT NULL,
    duplicate_uids    TEXT NOT NULL,
    opt_out_pre_json  TEXT NOT NULL,
    opt_out_post_json TEXT,
    status            TEXT NOT NULL,
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    started_at        TEXT NOT NULL,
    completed_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_merge_status ON merge_state(status);
"""


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def http_request(
    method: str, url: str, token: str, body: dict | None = None, timeout: float = 10.0
) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(payload)
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {"error": "non_json", "status": e.code}
        return e.code, payload


def open_db(db_path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA_MERGE_STATE)
    db.commit()
    return db


def load_cluster_members(db: sqlite3.Connection, cluster_id: str) -> list[dict] | None:
    # Cluster ID is a hash of the sorted uids — we resolve by joining via merge_state OR by
    # listing every cluster from the index and matching. Practically, the caller passes the
    # cluster_id from find_duplicates.py output, which includes the uid list.
    # If a merge_state row exists, use it. Otherwise reconstruct.
    row = db.execute(
        "SELECT primary_uid, duplicate_uids, natural_key, opt_out_pre_json FROM merge_state WHERE cluster_id = ?",
        (cluster_id,),
    ).fetchone()
    if row:
        primary_uid, dup_json, natural_key, pre_json = row
        uids = [primary_uid] + json.loads(dup_json)
    else:
        return None
    members = []
    for uid in uids:
        r = db.execute(
            """SELECT contact_uid, natural_key, name, email, field_count,
                      marketing_opt_out, sms_opt_out, email_opt_out, updated_at_podium
               FROM contact_index WHERE contact_uid = ?""",
            (uid,),
        ).fetchone()
        if r:
            members.append(
                {
                    "contact_uid": r[0],
                    "natural_key": r[1],
                    "name": r[2],
                    "email": r[3],
                    "field_count": r[4],
                    "marketing_opt_out": bool(r[5]),
                    "sms_opt_out": bool(r[6]),
                    "email_opt_out": bool(r[7]),
                    "updated_at_podium": r[8],
                }
            )
    return members


def build_cluster_from_index(db: sqlite3.Connection, cluster_id: str) -> list[dict] | None:
    # Walk every natural_key cluster; compute the cluster_id and match.
    rows = db.execute(
        """SELECT natural_key FROM contact_index
           WHERE deleted_at_podium IS NULL
           GROUP BY natural_key HAVING COUNT(*) >= 2"""
    ).fetchall()
    for (natural_key,) in rows:
        members = [
            {
                "contact_uid": r[0],
                "natural_key": r[1],
                "name": r[2],
                "email": r[3],
                "field_count": r[4],
                "marketing_opt_out": bool(r[5]),
                "sms_opt_out": bool(r[6]),
                "email_opt_out": bool(r[7]),
                "updated_at_podium": r[8],
            }
            for r in db.execute(
                """SELECT contact_uid, natural_key, name, email, field_count,
                          marketing_opt_out, sms_opt_out, email_opt_out, updated_at_podium
                   FROM contact_index
                   WHERE natural_key = ? AND deleted_at_podium IS NULL""",
                (natural_key,),
            ).fetchall()
        ]
        uids = sorted([m["contact_uid"] for m in members])
        h = hashlib.sha1("|".join(uids).encode()).hexdigest()[:12]
        if f"cl_{h}" == cluster_id:
            return members
    return None


def select_primary(members: list[dict]) -> dict:
    return max(
        members,
        key=lambda c: (c["field_count"], c["updated_at_podium"], -sum(ord(x) for x in c["contact_uid"])),
    )


def union_opt_outs(members: list[dict]) -> dict:
    return {
        "marketing_opt_out": any(m["marketing_opt_out"] for m in members),
        "sms_opt_out": any(m["sms_opt_out"] for m in members),
        "email_opt_out": any(m["email_opt_out"] for m in members),
    }


def append_audit(audit_path: Path, entry: dict) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def conflict_check(token: str, members: list[dict]) -> tuple[bool, str]:
    for m in members:
        status, body = http_request("GET", f"{PODIUM_BASE}/v4/contacts/{m['contact_uid']}", token)
        if status == 404:
            return False, f"contact_not_found: {m['contact_uid']}"
        if status != 200:
            return False, f"refetch_failed: {m['contact_uid']} -> {status}"
        live = body.get("data", body)
        live_updated = live.get("updated_at")
        if live_updated and live_updated != m["updated_at_podium"]:
            return False, (f"updated_at_drift: {m['contact_uid']} indexed={m['updated_at_podium']} live={live_updated}")
    return True, ""


def do_merge(
    db: sqlite3.Connection, audit_path: Path, members: list[dict], cluster_id: str, token: str, dry_run: bool
) -> int:
    primary = select_primary(members)
    duplicates = [m for m in members if m["contact_uid"] != primary["contact_uid"]]
    opt_out_pre = {
        m["contact_uid"]: {
            "marketing_opt_out": m["marketing_opt_out"],
            "sms_opt_out": m["sms_opt_out"],
            "email_opt_out": m["email_opt_out"],
        }
        for m in members
    }
    opt_out_union = union_opt_outs(members)

    plan = {
        "cluster_id": cluster_id,
        "primary_uid": primary["contact_uid"],
        "duplicate_uids": [d["contact_uid"] for d in duplicates],
        "opt_out_union": opt_out_union,
        "api_calls": (
            [f"GET /v4/contacts/{d['contact_uid']}   (conflict check)" for d in duplicates]
            + [
                f'POST /v4/contacts/{primary["contact_uid"]}/merge {{"duplicate_uids": '
                f"{json.dumps([d['contact_uid'] for d in duplicates])}}}",
                f"PATCH /v4/contacts/{primary['contact_uid']} {json.dumps(opt_out_union)}",
            ]
        ),
    }
    if dry_run:
        print(json.dumps({"cluster_id": cluster_id, "would_merge": plan, "would_not_call_podium": True}, indent=2))
        return 0

    # Persist pending state BEFORE any API call.
    db.execute(
        """INSERT OR REPLACE INTO merge_state
           (cluster_id, natural_key, primary_uid, duplicate_uids, opt_out_pre_json,
            status, attempts, started_at)
           VALUES (?, ?, ?, ?, ?, 'pending', 0, ?)""",
        (
            cluster_id,
            primary["natural_key"],
            primary["contact_uid"],
            json.dumps([d["contact_uid"] for d in duplicates]),
            json.dumps(opt_out_pre),
            now_iso(),
        ),
    )
    db.commit()

    # Conflict check.
    ok, reason = conflict_check(token, members)
    if not ok:
        db.execute(
            "UPDATE merge_state SET status='re_index_required', last_error=? WHERE cluster_id=?", (reason, cluster_id)
        )
        db.commit()
        append_audit(
            audit_path,
            {
                "ts": now_iso(),
                "event": "conflict_detected",
                "cluster_id": cluster_id,
                "reason": reason,
            },
        )
        sys.stderr.write(f"ERR_DEDUP_011 {reason}\n")
        return 4

    # Merge.
    db.execute("UPDATE merge_state SET status='merging', attempts=attempts+1 WHERE cluster_id=?", (cluster_id,))
    db.commit()
    status, body = http_request(
        "POST",
        f"{PODIUM_BASE}/v4/contacts/{primary['contact_uid']}/merge",
        token,
        body={"duplicate_uids": [d["contact_uid"] for d in duplicates]},
    )
    if status not in (200, 201, 204):
        db.execute(
            "UPDATE merge_state SET status='failed_permanent', last_error=? WHERE cluster_id=?",
            (json.dumps(body), cluster_id),
        )
        db.commit()
        append_audit(
            audit_path,
            {
                "ts": now_iso(),
                "event": "merge_failed",
                "cluster_id": cluster_id,
                "primary_uid": primary["contact_uid"],
                "status": status,
                "error": body,
            },
        )
        sys.stderr.write(f"merge failed {status}: {body}\n")
        return 1

    db.execute("UPDATE merge_state SET status='merged' WHERE cluster_id=?", (cluster_id,))
    db.commit()

    # Apply opt-out PATCH.
    status, body = http_request(
        "PATCH",
        f"{PODIUM_BASE}/v4/contacts/{primary['contact_uid']}",
        token,
        body=opt_out_union,
    )
    if status not in (200, 204):
        db.execute(
            "UPDATE merge_state SET status='compliance_failed', last_error=? WHERE cluster_id=?",
            (json.dumps(body), cluster_id),
        )
        db.commit()
        append_audit(
            audit_path,
            {
                "ts": now_iso(),
                "event": "compliance_failed",
                "cluster_id": cluster_id,
                "primary_uid": primary["contact_uid"],
                "opt_out_pre_merge": opt_out_pre,
                "opt_out_intended": opt_out_union,
                "status": status,
                "error": body,
            },
        )
        sys.stderr.write(
            f"ERR_DEDUP_010 opt_out_patch_failed {status}: {body}\n"
            "PAGE COMPLIANCE — opt-out flags may be in default state on the merged record\n"
        )
        return 5

    db.execute(
        "UPDATE merge_state SET status='patched', opt_out_post_json=?, completed_at=? WHERE cluster_id=?",
        (json.dumps(opt_out_union), now_iso(), cluster_id),
    )
    db.commit()

    append_audit(
        audit_path,
        {
            "ts": now_iso(),
            "event": "merge_complete",
            "cluster_id": cluster_id,
            "natural_key": primary["natural_key"],
            "primary_uid": primary["contact_uid"],
            "duplicate_uids": [d["contact_uid"] for d in duplicates],
            "opt_out_pre_merge": opt_out_pre,
            "opt_out_post_merge": opt_out_union,
            "soft_delete": True,
            "restorable": True,
        },
    )
    return 0


def resume(db: sqlite3.Connection, audit_path: Path, token: str) -> int:
    rows = db.execute(
        "SELECT cluster_id, primary_uid, status FROM merge_state "
        "WHERE status NOT IN ('patched','failed_permanent','compliance_failed','re_index_required')"
    ).fetchall()
    sys.stderr.write(f"resume: {len(rows)} non-terminal rows\n")
    for cluster_id, primary_uid, status in rows:
        members = load_cluster_members(db, cluster_id)
        if not members:
            sys.stderr.write(f"resume: cluster {cluster_id} members no longer in index, skipping\n")
            continue
        rc = do_merge(db, audit_path, members, cluster_id, token, dry_run=False)
        if rc != 0:
            sys.stderr.write(f"resume: cluster {cluster_id} returned {rc}\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cluster-id")
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--token-env", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--audit-log", default="./audit-log.jsonl", type=Path)
    args = ap.parse_args()

    token = os.environ.get(args.token_env, "")
    if not token and not args.dry_run:
        sys.stderr.write(f"missing env var {args.token_env}\n")
        return 3

    db = open_db(args.db)
    try:
        if args.resume:
            return resume(db, args.audit_log, token)
        if not args.cluster_id:
            sys.stderr.write("--cluster-id required when not --resume\n")
            return 3
        members = load_cluster_members(db, args.cluster_id) or build_cluster_from_index(db, args.cluster_id)
        if not members:
            sys.stderr.write(f"cluster {args.cluster_id} not found in index\n")
            return 3
        return do_merge(db, args.audit_log, members, args.cluster_id, token, dry_run=args.dry_run)
    except sqlite3.Error as e:
        sys.stderr.write(f"sqlite error: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
