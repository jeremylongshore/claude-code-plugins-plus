#!/usr/bin/env python3
"""cross_location_dedup.py — scan the natural-key index for duplicates spanning location_uids.

Usage:
  cross_location_dedup.py --db ./podium-dedup.sqlite \\
                          --output cross-location-review.json \\
                          [--policy review|auto_merge] \\
                          [--auto-merge-threshold 0.80]

Per-location dedup misses the case where the same phone exists as two contacts in two
different locations (the Sydney + Burleigh Heads case). This script runs AFTER per-location
runs and emits cross-location clusters to a human-review queue by default.

Default policy is `review` — never auto-merge across locations. Locations may represent
genuinely separate business entities, so auto-merging is opt-in per tenant.

Exit codes:
  0  success — review queue written (may be empty if no cross-location duplicates)
  2  local SQLite error
  3  missing required argument
"""

from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def cluster_id_for(uids: list[str]) -> str:
    h = hashlib.sha1("|".join(sorted(uids)).encode()).hexdigest()[:12]
    return f"cl_{h}"


def cluster_confidence(a: dict, b: dict) -> float:
    score = 0.60  # same natural_key
    if a.get("name") and a["name"].strip().lower() == (b.get("name") or "").strip().lower():
        score += 0.20
    if a.get("email") and a["email"].strip().lower() == (b.get("email") or "").strip().lower():
        score += 0.15
    a_tags = set(json.loads(a.get("tags_json") or "[]"))
    b_tags = set(json.loads(b.get("tags_json") or "[]"))
    if a_tags & b_tags:
        score += 0.05
    return round(min(score, 1.0), 4)


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


def find_cross_location_keys(db: sqlite3.Connection) -> list[str]:
    rows = db.execute(
        """SELECT natural_key
           FROM contact_index
           WHERE deleted_at_podium IS NULL
           GROUP BY natural_key
           HAVING COUNT(DISTINCT location_uid) > 1"""
    ).fetchall()
    return [r[0] for r in rows]


def load_members(db: sqlite3.Connection, natural_key: str) -> list[dict]:
    rows = db.execute(
        """SELECT contact_uid, location_uid, name, email, tags_json, field_count,
                  marketing_opt_out, sms_opt_out, email_opt_out, updated_at_podium
           FROM contact_index
           WHERE natural_key = ? AND deleted_at_podium IS NULL""",
        (natural_key,),
    ).fetchall()
    return [
        {
            "contact_uid": r[0],
            "location_uid": r[1],
            "name": r[2],
            "email": r[3],
            "tags_json": r[4],
            "field_count": r[5],
            "marketing_opt_out": bool(r[6]),
            "sms_opt_out": bool(r[7]),
            "email_opt_out": bool(r[8]),
            "updated_at_podium": r[9],
        }
        for r in rows
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--policy", choices=("review", "auto_merge"), default="review")
    ap.add_argument("--auto-merge-threshold", type=float, default=0.80)
    args = ap.parse_args()

    try:
        db = sqlite3.connect(args.db)
    except sqlite3.Error as e:
        sys.stderr.write(f"sqlite open: {e}\n")
        return 2

    try:
        keys = find_cross_location_keys(db)
    except sqlite3.Error as e:
        sys.stderr.write(f"sqlite query: {e}\n")
        return 2

    sys.stderr.write(f"cross_location_dedup: {len(keys)} natural_keys span multiple locations\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(args.output, "w") as f:
        for natural_key in keys:
            members = load_members(db, natural_key)
            if len(members) < 2:
                continue
            worst = 1.0
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    worst = min(worst, cluster_confidence(members[i], members[j]))
            primary = select_primary(members)
            uids = [m["contact_uid"] for m in members]
            cluster = {
                "cluster_id": cluster_id_for(uids),
                "natural_key": natural_key,
                "confidence": worst,
                "review_reason": "cross_location",
                "policy": args.policy,
                "members": [
                    {
                        "contact_uid": m["contact_uid"],
                        "location_uid": m["location_uid"],
                        "name": m.get("name"),
                        "email": m.get("email"),
                        "field_count": m["field_count"],
                        "updated_at_podium": m["updated_at_podium"],
                        "marketing_opt_out": m["marketing_opt_out"],
                        "sms_opt_out": m["sms_opt_out"],
                        "email_opt_out": m["email_opt_out"],
                    }
                    for m in members
                ],
                "suggested_primary_uid": primary["contact_uid"],
                "opt_out_union_if_merged": union_opt_outs(members),
                "auto_merge_eligible": (args.policy == "auto_merge" and worst >= args.auto_merge_threshold),
            }
            f.write(json.dumps(cluster) + "\n")
            written += 1

    sys.stderr.write(f"wrote {written} clusters to {args.output}\n")
    if args.policy == "review" and written > 0:
        sys.stderr.write(
            "policy=review: no cross-location merges executed. "
            "Operator must review the queue and confirm per cluster.\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
