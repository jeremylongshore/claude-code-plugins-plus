# HubSpot Contact Deduplication — Implementation Guide

Production Python pipeline for deduplicating millions of contacts, fuzzy matching with normalization, batched merge execution with rate-limit safety, and post-merge association cleanup runbook. TypeScript patterns and single-pair merge logic live in `SKILL.md`; this document covers the full pipeline architecture.

---

## Pipeline Architecture

A production dedup pipeline for large catalogs (500K–10M contacts) runs in four stages. Each stage is independent and resumable from a checkpoint file so a mid-run rate-limit stop does not require starting over.

```
Stage 1: Scan        → Extract all contacts from HubSpot into a local SQLite DB
Stage 2: Pair        → Generate candidate pairs using normalized properties + fuzzy matching
Stage 3: Qualify     → Score pairs, check compliance, emit merge plan
Stage 4: Execute     → Merge approved pairs, verify post-merge state, re-parent orphans
```

All stages read from and write to a local SQLite database (`dedup_run.db`) so the pipeline is observable, restartable, and auditable.

---

## Stage 1: Full Contact Scan

```python
#!/usr/bin/env python3
"""Stage 1 — Extract all contacts from HubSpot into local SQLite.

Usage: python3 stage1_scan.py --token {your-token} [--resume]
"""

import argparse
import json
import sqlite3
import time
from typing import Generator

import requests

PROPERTIES = [
    "email", "phone", "firstname", "lastname",
    "createdate", "lastmodifieddate",
    "lifecyclestage", "hs_email_optout",
    "hs_email_optout_date", "hs_email_hard_bounce_reason_enum",
    "hs_legal_basis", "hs_additional_emails",
]

SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
BATCH_READ_URL = "https://api.hubapi.com/crm/v3/objects/contacts/batch/read"


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            hs_id TEXT PRIMARY KEY,
            email TEXT,
            email_normalized TEXT,
            phone_e164 TEXT,
            firstname TEXT,
            lastname TEXT,
            createdate TEXT,
            lastmodifieddate TEXT,
            lifecyclestage TEXT,
            email_optout INTEGER DEFAULT 0,
            email_optout_date TEXT,
            hard_bounce INTEGER DEFAULT 0,
            gdpr_legal_basis TEXT,
            raw_json TEXT
        );
        CREATE TABLE IF NOT EXISTS scan_checkpoint (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    return conn


def normalize_email(raw: str) -> str:
    """Normalize email for dedup comparison. HubSpot uniqueness uses raw; we use normalized."""
    if not raw:
        return ""
    lower = raw.strip().lower()
    # googlemail.com and gmail.com deliver to the same inbox
    lower = lower.replace("@googlemail.com", "@gmail.com")
    local, _, domain = lower.partition("@")
    if domain == "gmail.com":
        # Gmail ignores dots in local part and everything after a +
        local = local.split("+")[0].replace(".", "")
    return f"{local}@{domain}" if domain else lower


def normalize_phone(raw: str, default_region: str = "US") -> str | None:
    """Normalize phone to E.164. Returns None if unparseable."""
    if not raw or not raw.strip():
        return None
    try:
        import phonenumbers
        parsed = phonenumbers.parse(raw.strip(), default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return None


def stream_pages(
    token: str,
    after: str | None = None,
    page_size: int = 100,
) -> Generator[list[dict], None, None]:
    """Stream all contacts in pages of page_size. Yields lists of raw result dicts."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    while True:
        body: dict = {
            "filterGroups": [],
            "properties": PROPERTIES,
            "limit": page_size,
        }
        if after:
            body["after"] = after

        for attempt in range(4):
            resp = requests.post(SEARCH_URL, headers=headers, json=body, timeout=30)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", "10"))
                print(f"  Rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                wait = min(60, 5 * (2 ** attempt))
                print(f"  Server error {resp.status_code} — retry in {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        yield results

        paging = data.get("paging", {})
        after = paging.get("next", {}).get("after")
        if not after:
            break


def upsert_contact(conn: sqlite3.Connection, result: dict) -> None:
    p = result.get("properties", {})
    hs_id = result["id"]
    email_raw = p.get("email", "") or ""
    bounce_raw = p.get("hs_email_hard_bounce_reason_enum", "")

    conn.execute("""
        INSERT OR REPLACE INTO contacts
            (hs_id, email, email_normalized, phone_e164, firstname, lastname,
             createdate, lastmodifieddate, lifecyclestage,
             email_optout, email_optout_date, hard_bounce, gdpr_legal_basis, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        hs_id,
        email_raw,
        normalize_email(email_raw),
        normalize_phone(p.get("phone", "") or ""),
        p.get("firstname", ""),
        p.get("lastname", ""),
        p.get("createdate", ""),
        p.get("lastmodifieddate", ""),
        p.get("lifecyclestage", ""),
        1 if p.get("hs_email_optout") == "true" else 0,
        p.get("hs_email_optout_date", ""),
        1 if bounce_raw else 0,
        p.get("hs_legal_basis", ""),
        json.dumps(result),
    ))


def run_scan(token: str, db_path: str, resume: bool) -> None:
    conn = init_db(db_path)
    after = None

    if resume:
        row = conn.execute("SELECT value FROM scan_checkpoint WHERE key='after'").fetchone()
        if row:
            after = row["value"]
            print(f"Resuming scan from cursor: {after}")

    total = 0
    try:
        for page in stream_pages(token, after=after):
            for result in page:
                upsert_contact(conn, result)
            total += len(page)
            after = None  # Will be updated from the last page's cursor

            conn.execute(
                "INSERT OR REPLACE INTO scan_checkpoint (key, value) VALUES ('after', ?)",
                (after,),
            )
            conn.commit()
            print(f"  Scanned {total} contacts...")
    finally:
        conn.close()
    print(f"Scan complete: {total} contacts written to {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--db", default="dedup_run.db")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run_scan(args.token, args.db, args.resume)
```

---

## Stage 2: Candidate Pair Generation with Fuzzy Matching

```python
#!/usr/bin/env python3
"""Stage 2 — Generate candidate duplicate pairs from local DB.

Uses normalized email (exact match in SQLite), phone E.164 (exact match),
and name similarity (rapidfuzz token_sort_ratio) to find duplicates.
Does NOT call HubSpot API — works entirely on the local snapshot.

Usage: python3 stage2_pair.py [--db dedup_run.db]
"""

import sqlite3
import itertools
from dataclasses import dataclass, field

try:
    from rapidfuzz import fuzz
except ImportError:
    raise SystemExit("pip install rapidfuzz is required for fuzzy name matching")


AUTO_MERGE_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.70

LIFECYCLE_ORDER = [
    "subscriber", "lead", "marketingqualifiedlead",
    "salesqualifiedlead", "opportunity", "customer", "evangelist",
]


@dataclass
class CandidatePair:
    id_a: str
    id_b: str
    email_match: bool
    phone_match: bool
    name_similarity: float
    confidence: float
    disposition: str  # "auto_merge" | "review" | "skip"

    def to_row(self) -> tuple:
        return (
            self.id_a, self.id_b,
            int(self.email_match), int(self.phone_match),
            round(self.name_similarity, 4),
            round(self.confidence, 4),
            self.disposition,
        )


def score_pair(a: sqlite3.Row, b: sqlite3.Row) -> CandidatePair:
    email_match = bool(
        a["email_normalized"]
        and b["email_normalized"]
        and a["email_normalized"] == b["email_normalized"]
    )

    phone_match = bool(
        a["phone_e164"]
        and b["phone_e164"]
        and a["phone_e164"] == b["phone_e164"]
    )

    name_a = f"{a['firstname'] or ''} {a['lastname'] or ''}".strip()
    name_b = f"{b['firstname'] or ''} {b['lastname'] or ''}".strip()
    name_sim = 0.0
    if name_a and name_b:
        name_sim = fuzz.token_sort_ratio(name_a.lower(), name_b.lower()) / 100.0

    confidence = 0.0
    if email_match:
        confidence += 0.80
    if phone_match:
        confidence += 0.50
    confidence += name_sim * 0.30
    confidence = min(confidence, 1.0)

    if confidence >= AUTO_MERGE_THRESHOLD:
        disposition = "auto_merge"
    elif confidence >= REVIEW_THRESHOLD:
        disposition = "review"
    else:
        disposition = "skip"

    return CandidatePair(
        id_a=a["hs_id"],
        id_b=b["hs_id"],
        email_match=email_match,
        phone_match=phone_match,
        name_similarity=name_sim,
        confidence=confidence,
        disposition=disposition,
    )


def init_pairs_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS candidate_pairs (
            id_a TEXT,
            id_b TEXT,
            email_match INTEGER,
            phone_match INTEGER,
            name_similarity REAL,
            confidence REAL,
            disposition TEXT,
            PRIMARY KEY (id_a, id_b)
        );
    """)
    conn.commit()


def find_email_groups(conn: sqlite3.Connection) -> list[list[sqlite3.Row]]:
    """Return groups of contacts sharing the same normalized email (2+ members)."""
    cursor = conn.execute("""
        SELECT email_normalized, COUNT(*) as cnt
        FROM contacts
        WHERE email_normalized != ''
        GROUP BY email_normalized
        HAVING cnt > 1
    """)
    groups = []
    for row in cursor.fetchall():
        members = conn.execute(
            "SELECT * FROM contacts WHERE email_normalized = ?",
            (row["email_normalized"],),
        ).fetchall()
        groups.append(members)
    return groups


def find_phone_groups(conn: sqlite3.Connection) -> list[list[sqlite3.Row]]:
    """Return groups of contacts sharing the same E.164 phone (2+ members)."""
    cursor = conn.execute("""
        SELECT phone_e164, COUNT(*) as cnt
        FROM contacts
        WHERE phone_e164 IS NOT NULL AND phone_e164 != ''
        GROUP BY phone_e164
        HAVING cnt > 1
    """)
    groups = []
    for row in cursor.fetchall():
        members = conn.execute(
            "SELECT * FROM contacts WHERE phone_e164 = ?",
            (row["phone_e164"],),
        ).fetchall()
        groups.append(members)
    return groups


def run_pairing(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_pairs_table(conn)

    inserted = 0

    def process_groups(groups: list[list[sqlite3.Row]]) -> None:
        nonlocal inserted
        for group in groups:
            for a, b in itertools.combinations(group, 2):
                pair = score_pair(a, b)
                if pair.disposition == "skip":
                    continue
                conn.execute("""
                    INSERT OR IGNORE INTO candidate_pairs
                        (id_a, id_b, email_match, phone_match, name_similarity, confidence, disposition)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, pair.to_row())
                inserted += 1

    print("Finding email duplicate groups...")
    email_groups = find_email_groups(conn)
    process_groups(email_groups)
    print(f"  Email groups: {len(email_groups)}")

    print("Finding phone duplicate groups...")
    phone_groups = find_phone_groups(conn)
    process_groups(phone_groups)
    print(f"  Phone groups: {len(phone_groups)}")

    conn.commit()
    conn.close()
    print(f"Pairing complete: {inserted} candidate pairs written")
    print(f"  Run: sqlite3 {db_path} \"SELECT disposition, COUNT(*) FROM candidate_pairs GROUP BY disposition;\"")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="dedup_run.db")
    args = parser.parse_args()
    run_pairing(args.db)
```

---

## Stage 3: Compliance Qualification and Merge Plan

```python
#!/usr/bin/env python3
"""Stage 3 — Qualify candidate pairs for compliance and emit merge plan.

Reads candidate_pairs from the local DB. For each auto_merge pair, determines
primary/secondary and checks compliance rules. Emits a merge_plan table.

Usage: python3 stage3_qualify.py [--db dedup_run.db]
"""

import sqlite3
import json
from datetime import datetime

TEST_EMAIL_DOMAINS = frozenset([
    "mailinator.com", "example.com", "test.com", "yopmail.com",
    "guerrillamail.com", "throwam.com", "trashmail.com", "tempmail.com",
])

LIFECYCLE_ORDER = [
    "subscriber", "lead", "marketingqualifiedlead",
    "salesqualifiedlead", "opportunity", "customer", "evangelist",
]


def is_test_email(email: str) -> bool:
    domain = (email.split("@")[-1] or "").lower()
    return domain in TEST_EMAIL_DOMAINS


def pick_primary_id(a: dict, b: dict) -> tuple[str, str, str]:
    """Return (primary_id, secondary_id, reason)."""
    # 1. Test email override
    a_test = is_test_email(a.get("email", ""))
    b_test = is_test_email(b.get("email", ""))
    if a_test and not b_test:
        return b["hs_id"], a["hs_id"], "test_email_override"
    if b_test and not a_test:
        return a["hs_id"], b["hs_id"], "test_email_override"

    # 2. Opt-out override — prefer opted-in as primary
    a_optout = bool(a.get("email_optout"))
    b_optout = bool(b.get("email_optout"))
    if a_optout and not b_optout:
        return b["hs_id"], a["hs_id"], "optout_override"
    if b_optout and not a_optout:
        return a["hs_id"], b["hs_id"], "optout_override"

    # 3. Default: oldest createdate is primary (most complete timeline)
    try:
        a_created = datetime.fromisoformat(a.get("createdate", "").replace("Z", "+00:00"))
        b_created = datetime.fromisoformat(b.get("createdate", "").replace("Z", "+00:00"))
        if a_created <= b_created:
            return a["hs_id"], b["hs_id"], "oldest_contact"
        else:
            return b["hs_id"], a["hs_id"], "oldest_contact"
    except (ValueError, TypeError):
        return a["hs_id"], b["hs_id"], "fallback"


def check_compliance(a: dict, b: dict) -> tuple[bool, str]:
    """Return (can_auto_merge, reason). False means queue for review."""
    if a.get("hard_bounce") or b.get("hard_bounce"):
        return False, "hard_bounce_present"
    if a.get("gdpr_legal_basis") and not b.get("gdpr_legal_basis"):
        return False, "gdpr_basis_asymmetry"
    if b.get("gdpr_legal_basis") and not a.get("gdpr_legal_basis"):
        return False, "gdpr_basis_asymmetry"
    return True, "ok"


def resolve_post_merge_optout(a: dict, b: dict) -> bool:
    """Conservative: if either is opted out, result should be opted out."""
    return bool(a.get("email_optout")) or bool(b.get("email_optout"))


def run_qualify(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS merge_plan (
            primary_id TEXT,
            secondary_id TEXT,
            selection_reason TEXT,
            expected_optout INTEGER,
            status TEXT DEFAULT 'pending',
            compliance_block TEXT,
            PRIMARY KEY (primary_id, secondary_id)
        );
    """)
    conn.commit()

    auto_merge_pairs = conn.execute(
        "SELECT * FROM candidate_pairs WHERE disposition = 'auto_merge'"
    ).fetchall()

    planned = 0
    blocked = 0

    for pair in auto_merge_pairs:
        a = dict(conn.execute("SELECT * FROM contacts WHERE hs_id = ?", (pair["id_a"],)).fetchone())
        b = dict(conn.execute("SELECT * FROM contacts WHERE hs_id = ?", (pair["id_b"],)).fetchone())

        can_merge, block_reason = check_compliance(a, b)
        if not can_merge:
            conn.execute("""
                UPDATE candidate_pairs SET disposition = 'review'
                WHERE id_a = ? AND id_b = ?
            """, (pair["id_a"], pair["id_b"]))
            blocked += 1
            continue

        primary_id, secondary_id, selection_reason = pick_primary_id(a, b)
        expected_optout = resolve_post_merge_optout(a, b)

        conn.execute("""
            INSERT OR IGNORE INTO merge_plan
                (primary_id, secondary_id, selection_reason, expected_optout, status, compliance_block)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (primary_id, secondary_id, selection_reason, int(expected_optout), ""))
        planned += 1

    conn.commit()
    conn.close()
    print(f"Qualify complete: {planned} pairs in merge plan, {blocked} escalated to review")
    print(f"  Human review queue: sqlite3 {db_path} \"SELECT * FROM candidate_pairs WHERE disposition='review';\"")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="dedup_run.db")
    args = parser.parse_args()
    run_qualify(args.db)
```

---

## Stage 4: Batched Merge Execution

```python
#!/usr/bin/env python3
"""Stage 4 — Execute merge plan with rate-limit safety and post-merge verification.

Usage: python3 stage4_execute.py --token {your-token} [--db dedup_run.db] [--dry-run]
"""

import argparse
import sqlite3
import time
import json
import requests

MERGE_URL = "https://api.hubapi.com/crm/v3/objects/contacts/merge"
CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts/{id}"

# Stop pipeline at 96% of daily quota to preserve headroom for non-dedup traffic
DAILY_QUOTA = 500_000
DAILY_STOP_AT = 480_000
BURST_LIMIT = 90  # Leave 10 req/10s buffer below the 100 req/10s cap
WINDOW_MS = 10_000

daily_calls_used = 0
window_start = time.monotonic()
window_calls = 0


def rate_gate() -> None:
    """Enforce burst rate limit: max BURST_LIMIT calls per 10 seconds."""
    global window_start, window_calls
    elapsed_ms = (time.monotonic() - window_start) * 1000
    if elapsed_ms >= WINDOW_MS:
        window_start = time.monotonic()
        window_calls = 0

    if window_calls >= BURST_LIMIT:
        sleep_s = (WINDOW_MS - elapsed_ms) / 1000 + 0.05
        time.sleep(max(sleep_s, 0))
        window_start = time.monotonic()
        window_calls = 0

    window_calls += 1


def check_daily_quota(resp: requests.Response) -> None:
    global daily_calls_used
    remaining = int(resp.headers.get("X-HubSpot-RateLimit-Daily-Remaining", DAILY_QUOTA))
    daily_calls_used = DAILY_QUOTA - remaining
    if daily_calls_used >= DAILY_STOP_AT:
        raise SystemExit(
            f"Daily quota at {daily_calls_used}/{DAILY_QUOTA} — stopping. "
            "Resume tomorrow or after midnight UTC reset."
        )


def do_merge(token: str, primary_id: str, secondary_id: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [dry-run] Would merge: primary={primary_id} secondary={secondary_id}")
        return True

    for attempt in range(3):
        rate_gate()
        resp = requests.post(
            MERGE_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"primaryObjectId": primary_id, "objectIdToMerge": secondary_id},
            timeout=30,
        )
        check_daily_quota(resp)

        if resp.status_code == 200:
            return True
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "10"))
            print(f"  429 rate limited — waiting {wait}s")
            time.sleep(wait)
            continue
        if resp.status_code in (409,) and "MERGE_IN_PROGRESS" in (resp.text or ""):
            time.sleep(30)
            continue
        if resp.status_code >= 500:
            wait = min(60, 5 * (2 ** attempt))
            print(f"  {resp.status_code} server error — retry in {wait}s")
            time.sleep(wait)
            continue

        # Non-retryable error
        body = resp.json() if resp.content else {}
        print(f"  Merge failed {resp.status_code}: {body.get('message', resp.text)}")
        return False

    return False


def verify_optout(token: str, contact_id: str, expected: bool) -> None:
    """Read post-merge contact and patch hs_email_optout if it doesn't match expected."""
    rate_gate()
    resp = requests.get(
        f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"properties": "hs_email_optout"},
        timeout=15,
    )
    if not resp.ok:
        print(f"  WARNING: could not verify optout for {contact_id}: {resp.status_code}")
        return

    actual = resp.json().get("properties", {}).get("hs_email_optout") == "true"
    if actual != expected:
        rate_gate()
        patch = requests.patch(
            f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"properties": {"hs_email_optout": str(expected).lower()}},
            timeout=15,
        )
        if patch.ok:
            print(f"  Patched optout on {contact_id}: was {actual}, set to {expected}")
        else:
            print(f"  WARNING: optout patch failed on {contact_id}: {patch.status_code}")


def run_execute(token: str, db_path: str, dry_run: bool) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    pending = conn.execute(
        "SELECT * FROM merge_plan WHERE status = 'pending' ORDER BY rowid"
    ).fetchall()

    print(f"Executing {len(pending)} merges (dry_run={dry_run})")

    success = error = 0
    for row in pending:
        primary_id = row["primary_id"]
        secondary_id = row["secondary_id"]
        expected_optout = bool(row["expected_optout"])

        ok = do_merge(token, primary_id, secondary_id, dry_run)

        if ok:
            if not dry_run:
                verify_optout(token, primary_id, expected_optout)
            conn.execute(
                "UPDATE merge_plan SET status = 'done' WHERE primary_id = ? AND secondary_id = ?",
                (primary_id, secondary_id),
            )
            success += 1
        else:
            conn.execute(
                "UPDATE merge_plan SET status = 'error' WHERE primary_id = ? AND secondary_id = ?",
                (primary_id, secondary_id),
            )
            error += 1

        if (success + error) % 100 == 0:
            conn.commit()
            print(f"  Progress: {success} done, {error} errors")

    conn.commit()
    conn.close()
    print(f"Execute complete: {success} merged, {error} errors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--db", default="dedup_run.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_execute(args.token, args.db, args.dry_run)
```

---

## Post-Merge Association Cleanup Runbook

Run this after Stage 4 completes. The script audits all merged contacts' pre-merge association snapshots (written during Stage 3) and re-parents any that did not transfer.

```python
#!/usr/bin/env python3
"""Post-merge association cleanup.

For each completed merge, checks that all associations from the secondary
contact now exist on the primary. Re-parents orphans via the v4 associations API.

Usage: python3 association_cleanup.py --token {your-token} [--db dedup_run.db]
"""

import argparse
import sqlite3
import time
import requests

ASSOC_READ_URL = "https://api.hubapi.com/crm/v4/objects/contacts/{id}/associations/{to_type}"
ASSOC_WRITE_URL = "https://api.hubapi.com/crm/v4/objects/contacts/{from_id}/associations/{to_type}/{to_id}"

OBJECT_TYPES = ["deals", "companies", "tickets", "notes", "tasks", "calls", "emails", "meetings"]

# Association type IDs for contact-to-object (HUBSPOT_DEFINED category)
ASSOC_TYPE_IDS = {
    "companies": 1,
    "deals": 3,
    "tickets": 15,
    "calls": 193,
    "emails": 197,
    "notes": 201,
    "tasks": 204,
    "meetings": 200,
}


def get_associations(token: str, contact_id: str, object_type: str) -> set[str]:
    resp = requests.get(
        ASSOC_READ_URL.format(id=contact_id, to_type=object_type),
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if resp.status_code == 404:
        return set()
    resp.raise_for_status()
    return {str(r["toObjectId"]) for r in resp.json().get("results", [])}


def create_association(
    token: str, primary_id: str, object_type: str, to_id: str
) -> bool:
    type_id = ASSOC_TYPE_IDS.get(object_type, 1)
    resp = requests.put(
        ASSOC_WRITE_URL.format(from_id=primary_id, to_type=object_type, to_id=to_id),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=[{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": type_id}],
        timeout=15,
    )
    return resp.ok


def run_cleanup(token: str, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    done_merges = conn.execute(
        "SELECT primary_id, secondary_id FROM merge_plan WHERE status = 'done'"
    ).fetchall()

    print(f"Auditing associations for {len(done_merges)} completed merges")
    total_orphans = total_repaired = 0

    for merge in done_merges:
        primary_id = merge["primary_id"]
        secondary_id = merge["secondary_id"]

        for obj_type in OBJECT_TYPES:
            try:
                primary_assocs = get_associations(token, primary_id, obj_type)
                secondary_assocs = get_associations(token, secondary_id, obj_type)
                time.sleep(0.12)  # ~8 calls/s — stay well under the 100/10s limit
            except requests.HTTPError as e:
                print(f"  WARNING: could not read {obj_type} associations for {secondary_id}: {e}")
                continue

            orphans = secondary_assocs - primary_assocs
            for orphan_id in orphans:
                total_orphans += 1
                ok = create_association(token, primary_id, obj_type, orphan_id)
                if ok:
                    total_repaired += 1
                    print(f"  Repaired: {obj_type} {orphan_id} → contact {primary_id}")
                else:
                    print(f"  WARNING: could not re-parent {obj_type} {orphan_id} → {primary_id}")
                time.sleep(0.12)

    conn.close()
    print(f"Cleanup complete: {total_orphans} orphans found, {total_repaired} repaired")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--db", default="dedup_run.db")
    args = parser.parse_args()
    run_cleanup(args.token, args.db)
```

---

## Normalization Reference

### Email normalization edge cases

| Raw input | Normalized | Reason |
|---|---|---|
| `Jane.Doe@gmail.com` | `janedoe@gmail.com` | Lowercase + remove dots from Gmail local part |
| `jane+newsletters@gmail.com` | `jane@gmail.com` | Remove Gmail + alias tag |
| `jane@googlemail.com` | `jane@gmail.com` | googlemail.com and gmail.com are the same inbox |
| `JANE@EXAMPLE.COM` | `jane@example.com` | Lowercase only (non-Gmail domains keep dots) |
| `jane.doe@outlook.com` | `jane.doe@outlook.com` | Outlook does NOT ignore dots — preserve them |
| ` jane@example.com ` | `jane@example.com` | Strip leading/trailing whitespace |

### Phone normalization edge cases

| Raw input | E.164 output | Notes |
|---|---|---|
| `(512) 867-5309` | `+15128675309` | US default region applied |
| `512.867.5309` | `+15128675309` | Punctuation stripped |
| `+1-512-867-5309` | `+15128675309` | Country code preserved |
| `0044 20 7946 0958` | `+442079460958` | UK number with 00 prefix |
| `867-5309` | `None` | Too short — no default-region expansion for 7-digit numbers |
| `not a phone` | `None` | Unparseable — skip |

### Confidence scoring matrix

| Email match | Phone match | Name similarity | Confidence | Disposition |
|---|---|---|---|---|
| yes | yes | any | 1.0 (capped) | auto_merge |
| yes | no | ≥ 0.50 | 0.80–0.95 | auto_merge |
| yes | no | < 0.50 | 0.80 | auto_merge |
| no | yes | ≥ 0.70 | 0.71–0.85 | review or auto_merge |
| no | yes | < 0.70 | 0.50 | skip |
| no | no | ≥ 0.85 | 0.26 | skip |

Confidence formula: `min(email_match * 0.80 + phone_match * 0.50 + name_sim * 0.30, 1.0)`

---

## Pipeline Execution Order

```bash
# Install dependencies
pip install requests phonenumbers rapidfuzz

# Run all four stages sequentially
python3 stage1_scan.py --token {your-token} --db dedup_run.db
python3 stage2_pair.py --db dedup_run.db
python3 stage3_qualify.py --db dedup_run.db

# Dry run first to review the plan
python3 stage4_execute.py --token {your-token} --db dedup_run.db --dry-run

# Inspect the dry-run output, then execute
python3 stage4_execute.py --token {your-token} --db dedup_run.db

# Post-merge association audit and repair
python3 association_cleanup.py --token {your-token} --db dedup_run.db
```

### Checkpoint and resume

Stage 1 checkpoints the search cursor after each page. If the scan is interrupted by a rate limit or timeout, re-run with `--resume`:

```bash
python3 stage1_scan.py --token {your-token} --db dedup_run.db --resume
```

Stages 2–4 are naturally idempotent: they use `INSERT OR IGNORE` and `UPDATE WHERE status='pending'`, so re-running skips already-processed rows.

### Audit queries

```bash
# Overview of dedup run
sqlite3 dedup_run.db "
  SELECT
    (SELECT COUNT(*) FROM contacts) AS total_contacts,
    (SELECT COUNT(*) FROM candidate_pairs WHERE disposition='auto_merge') AS auto_merge,
    (SELECT COUNT(*) FROM candidate_pairs WHERE disposition='review') AS for_review,
    (SELECT COUNT(*) FROM merge_plan WHERE status='done') AS merged,
    (SELECT COUNT(*) FROM merge_plan WHERE status='error') AS errors;
"

# Review queue — inspect before any human decisions
sqlite3 dedup_run.db "
  SELECT cp.id_a, cp.id_b, cp.confidence, cp.email_match, cp.phone_match, cp.name_similarity
  FROM candidate_pairs cp
  WHERE cp.disposition = 'review'
  ORDER BY cp.confidence DESC
  LIMIT 50;
"

# Error log
sqlite3 dedup_run.db "SELECT * FROM merge_plan WHERE status='error';"
```

---

## Time Estimates at Scale

| Catalog size | Scan time (Stage 1) | Pair time (Stage 2) | Execute time (Stage 4) |
|---|---|---|---|
| 100K contacts | ~3 min | <1 min | ~15 min (assuming 5% dup rate) |
| 500K contacts | ~15 min | ~2 min | ~75 min |
| 1M contacts | ~30 min | ~5 min | ~2.5 hours |
| 5M contacts | ~2.5 hours | ~20 min | ~12.5 hours (multi-day across quota resets) |

Stage 4 time assumes 5% duplicate rate, single-threaded at 90 req/10s with one merge call per pair. For catalogs where a significant proportion of contacts share emails (post-CSV-storm), the merge count will be higher and execution time will increase proportionally.

For catalogs over 500K, run Stage 4 in a background process with output redirected to a log file:

```bash
nohup python3 stage4_execute.py --token {your-token} --db dedup_run.db > execute.log 2>&1 &
tail -f execute.log
```
