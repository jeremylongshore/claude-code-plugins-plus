# HubSpot Lifecycle and Lists — Implementation Guide

## Overview

This guide provides production-ready Python implementations for the six failure modes covered in the main skill. Each section is self-contained and can be dropped into an existing integration. All code requires Python 3.10+, uses only the standard library, and carries no external dependencies.

---

## 1. Lifecycle Stage Progression Guard

### Design rationale

The guard must operate as a pre-check, not as a post-flight comparison. Making the API call and then trying to undo a regression is not safe — the HubSpot webhook fires on the write, downstream automations trigger, and the regression is visible in the portal before the correction lands. The guard reads the current stage, validates the proposed transition, and raises before the PATCH is issued.

The guard also needs to handle the `other` lateral stage correctly. `other` is not position 8 in the linear sequence — it is a lateral assignment that can be made from any stage. A contact at `customer` who moves to `other` is not a regression. A contact at `other` who moves to `customer` is not a progression. The guard allows `other` assignments unconditionally.

### Full implementation

```python
"""
hubspot_lifecycle_guard.py

Lifecycle stage progression guard for HubSpot contacts.
Prevents regression without blocking lateral 'other' assignments.
"""

from __future__ import annotations
import json
import urllib.error
import urllib.request
import time
from typing import Optional


# Canonical linear stage order — internal enum values, not display labels
STAGE_ORDER: list[str] = [
    "subscriber",
    "lead",
    "marketingqualifiedlead",
    "salesqualifiedlead",
    "opportunity",
    "customer",
    "evangelist",
]

HUBSPOT_API_BASE = "https://api.hubapi.com"


class LifecycleRegressionError(ValueError):
    """Raised when a proposed stage transition would regress a contact."""
    def __init__(self, contact_id: str, current: str, proposed: str):
        self.contact_id = contact_id
        self.current = current
        self.proposed = proposed
        super().__init__(
            f"Lifecycle regression blocked for contact {contact_id}: "
            f"{current!r} (index {stage_index(current)}) → {proposed!r} "
            f"(index {stage_index(proposed)}). "
            f"To intentionally move a contact backward, call "
            f"patch_contact_lifecycle() directly and document the business reason."
        )


def stage_index(stage: str) -> int:
    """Return the linear position of a stage, or -1 if not in the linear sequence."""
    try:
        return STAGE_ORDER.index(stage.strip().lower())
    except ValueError:
        return -1  # 'other' or any unrecognized value


def is_progression_or_lateral(current: str, proposed: str) -> bool:
    """
    Return True if the transition is allowed:
    - proposed is 'other' (always lateral — allowed)
    - current is 'other' (leaving lateral — always allowed)
    - proposed index >= current index (forward or same)
    """
    if proposed.lower() == "other" or current.lower() == "other":
        return True
    current_idx = stage_index(current)
    proposed_idx = stage_index(proposed)
    # If either value is not in the linear set, allow (unknown custom stage)
    if current_idx == -1 or proposed_idx == -1:
        return True
    return proposed_idx >= current_idx


def _hubspot_get(path: str, token: str) -> dict:
    """Make a GET request to the HubSpot API and return the parsed JSON body."""
    req = urllib.request.Request(
        f"{HUBSPOT_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HubSpot GET {path} failed {exc.code}: {body}") from exc


def _hubspot_patch(path: str, payload: dict, token: str) -> dict:
    """Make a PATCH request to the HubSpot API and return the parsed JSON body."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{HUBSPOT_API_BASE}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HubSpot PATCH {path} failed {exc.code}: {body}") from exc


def get_contact_lifecycle(contact_id: str, token: str) -> str:
    """Return the current lifecyclestage value for a contact. Returns empty string if unset."""
    data = _hubspot_get(
        f"/crm/v3/objects/contacts/{contact_id}?properties=lifecyclestage",
        token,
    )
    return data["properties"].get("lifecyclestage") or ""


def patch_contact_lifecycle(contact_id: str, stage: str, token: str) -> dict:
    """Set lifecyclestage without the progression guard. Use only when intentional regression is documented."""
    return _hubspot_patch(
        f"/crm/v3/objects/contacts/{contact_id}",
        {"properties": {"lifecyclestage": stage}},
        token,
    )


def safe_set_lifecycle(
    contact_id: str,
    new_stage: str,
    token: str,
    allow_same: bool = True,
) -> dict:
    """
    Set a contact's lifecycle stage with a progression guard.

    Raises LifecycleRegressionError if new_stage would move the contact backward
    in the linear funnel. Lateral 'other' assignments are always allowed.

    Args:
        contact_id: HubSpot contact VID or object ID
        new_stage:  Target lifecycle stage (internal enum value)
        token:      HubSpot private app token or OAuth access token
        allow_same: If False, raise on same-stage writes (idempotency enforcement).
                    Default True — same-stage writes are silently allowed.

    Returns:
        The updated contact object from HubSpot.
    """
    current = get_contact_lifecycle(contact_id, token)
    current_norm = (current or "").strip().lower()
    new_norm = new_stage.strip().lower()

    if not allow_same and current_norm == new_norm:
        raise ValueError(
            f"Contact {contact_id} is already at stage {current_norm!r}. "
            f"No update needed."
        )

    if not is_progression_or_lateral(current_norm, new_norm):
        raise LifecycleRegressionError(contact_id, current_norm, new_norm)

    return patch_contact_lifecycle(contact_id, new_norm, token)


def bulk_safe_set_lifecycle(
    updates: list[dict],  # [{"id": "123", "stage": "customer"}, ...]
    token: str,
    dry_run: bool = False,
) -> dict:
    """
    Apply lifecycle stage updates with progression guard across multiple contacts.

    Args:
        updates:  List of dicts with 'id' and 'stage' keys.
        token:    HubSpot token.
        dry_run:  If True, validate all transitions without making API calls.

    Returns:
        {"applied": [...], "blocked": [...], "dry_run": bool}
    """
    applied = []
    blocked = []

    for item in updates:
        contact_id = str(item["id"])
        new_stage = item["stage"]
        try:
            if dry_run:
                current = get_contact_lifecycle(contact_id, token)
                if not is_progression_or_lateral(current, new_stage):
                    raise LifecycleRegressionError(contact_id, current, new_stage)
                applied.append({"id": contact_id, "stage": new_stage, "current": current})
            else:
                result = safe_set_lifecycle(contact_id, new_stage, token)
                applied.append({"id": contact_id, "stage": new_stage})
        except LifecycleRegressionError as exc:
            blocked.append({
                "id": contact_id,
                "current": exc.current,
                "proposed": exc.proposed,
                "reason": str(exc),
            })
        except Exception as exc:
            blocked.append({"id": contact_id, "proposed": new_stage, "reason": str(exc)})

    return {"applied": applied, "blocked": blocked, "dry_run": dry_run}
```

### Usage

```python
import os
from hubspot_lifecycle_guard import safe_set_lifecycle, bulk_safe_set_lifecycle

TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"]

# Single contact — will raise if regression detected
try:
    result = safe_set_lifecycle("12345", "customer", TOKEN)
    print(f"Updated: {result['properties']['lifecyclestage']}")
except ValueError as exc:
    print(f"Blocked: {exc}")

# Bulk dry run — validate without writing
report = bulk_safe_set_lifecycle(
    [
        {"id": "12345", "stage": "salesqualifiedlead"},
        {"id": "67890", "stage": "subscriber"},  # this will be blocked
    ],
    TOKEN,
    dry_run=True,
)
print(f"Would apply: {len(report['applied'])}, Would block: {len(report['blocked'])}")
for b in report["blocked"]:
    print(f"  BLOCK {b['id']}: {b['reason']}")
```

---

## 2. Dynamic List Criteria Builder

### Design rationale

The v1 list filter syntax is underdocumented and inconsistent with the v3 CRM search filter syntax. This builder produces valid v1 filter objects from a simpler dict-based input format and handles the nesting correctly (outer OR, inner AND).

The builder also tracks which lists have had criteria edited recently and provides a polling helper to detect when the background re-evaluation job has finished.

```python
"""
hubspot_list_builder.py

Build and manage dynamic HubSpot lists via the v1 Contacts Lists API.
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Literal

HUBSPOT_API_BASE = "https://api.hubapi.com"


@dataclass
class ContactPropertyFilter:
    """A single filter on a contact property."""
    property: str
    operation: Literal[
        "SET_ANY", "NOT_IN", "IS_ANY", "IS_NOT_ANY",
        "BEGINS_WITH_ANY", "ENDS_WITH_ANY", "CONTAINS", "EQ", "LT", "GT"
    ]
    value: str = ""
    type: str = "string"
    within_time_mode: str = ""

    def to_dict(self) -> dict:
        d: dict = {
            "filterFamily": "ContactProperty",
            "type": self.type,
            "property": self.property,
            "operation": self.operation,
        }
        if self.value:
            d["value"] = self.value
        if self.within_time_mode:
            d["withinTimeMode"] = self.within_time_mode
        return d


@dataclass
class ListMembershipFilter:
    """Filter: contact is a member of another list."""
    list_id: int
    operator: Literal["IN_LIST", "NOT_IN_LIST"] = "IN_LIST"

    def to_dict(self) -> dict:
        return {
            "filterFamily": "ListMembership",
            "operator": self.operator,
            "listId": self.list_id,
        }


def build_filter_groups(
    and_groups: list[list[ContactPropertyFilter | ListMembershipFilter]],
) -> list[list[dict]]:
    """
    Convert filter groups to the v1 API wire format.

    and_groups is a list of filter groups:
    - Filters within a group are AND'd together.
    - Groups are OR'd with each other.

    Example: (A AND B) OR (C) → [[A, B], [C]]
    """
    return [[f.to_dict() for f in group] for group in and_groups]


def _api_post(path: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{HUBSPOT_API_BASE}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"POST {path} failed {exc.code}: {exc.read().decode()}") from exc


def _api_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{HUBSPOT_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def create_dynamic_list(
    name: str,
    filter_groups: list[list[ContactPropertyFilter | ListMembershipFilter]],
    token: str,
) -> dict:
    """Create a dynamic list with the given criteria. Returns the created list metadata."""
    payload = {
        "name": name,
        "dynamic": True,
        "filters": build_filter_groups(filter_groups),
    }
    return _api_post("/contacts/v1/lists", payload, token)


def wait_for_list_refresh(
    list_id: int,
    token: str,
    timeout_s: int = 7200,
    poll_interval_s: int = 60,
) -> dict:
    """
    Poll a dynamic list until its processing status is DONE.

    Returns the final list metadata.
    Raises TimeoutError if the list does not finish refreshing within timeout_s.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        meta = _api_get(f"/contacts/v1/lists/{list_id}", token)
        status = meta.get("metaData", {}).get("processing", "UNKNOWN")
        if status == "DONE":
            return meta
        print(f"List {list_id} processing status: {status}. Waiting {poll_interval_s}s...")
        time.sleep(poll_interval_s)
    raise TimeoutError(
        f"List {list_id} did not finish refreshing within {timeout_s}s. "
        f"Check HubSpot status page and consider suppressing automations until refresh completes."
    )
```

### Usage

```python
from hubspot_list_builder import ContactPropertyFilter, create_dynamic_list, wait_for_list_refresh
import os

TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"]

# Create a dynamic list: (MQL OR SQL) who opted in for email
filter_groups = [
    [
        ContactPropertyFilter("lifecyclestage", "SET_ANY", "marketingqualifiedlead"),
        ContactPropertyFilter("hs_email_optout", "NOT_IN", "true", type="bool"),
    ],
    [
        ContactPropertyFilter("lifecyclestage", "SET_ANY", "salesqualifiedlead"),
        ContactPropertyFilter("hs_email_optout", "NOT_IN", "true", type="bool"),
    ],
]

result = create_dynamic_list("MQL + SQL — Email Opted In", filter_groups, TOKEN)
list_id = result["listId"]
print(f"Created list {list_id}")

# Wait for initial evaluation to complete before trusting membership
final = wait_for_list_refresh(list_id, TOKEN, timeout_s=3600, poll_interval_s=120)
print(f"List ready. Member count: {final['metaData']['size']}")
```

---

## 3. Static List Batch Membership Manager

```python
"""
hubspot_static_list.py

Batch membership management for HubSpot static lists.
Includes orphan detection, deduplication, and idempotent add/remove.
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error

HUBSPOT_API_BASE = "https://api.hubapi.com"
BATCH_SIZE = 100  # HubSpot recommends 100; supports up to 500


def _api_post(path: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{HUBSPOT_API_BASE}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"POST {path} failed {exc.code}: {exc.read().decode()}") from exc


def get_all_list_vids(list_id: int, token: str) -> set[int]:
    """Paginate through all contacts in a list and return their VIDs."""
    vids: set[int] = set()
    offset: int | None = None
    while True:
        url = (
            f"{HUBSPOT_API_BASE}/contacts/v1/lists/{list_id}/contacts/all"
            f"?count={BATCH_SIZE}"
        )
        if offset is not None:
            url += f"&vidOffset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        for contact in data.get("contacts", []):
            vids.add(int(contact["vid"]))
        if not data.get("has-more", False):
            break
        offset = int(data["vid-offset"])
    return vids


def add_to_static_list(
    list_id: int,
    vids: list[int],
    token: str,
    rate_limit_delay_s: float = 0.1,
) -> dict:
    """
    Add contacts to a static list in batches of BATCH_SIZE.

    Returns a summary of how many were newly added vs already present (discarded).
    Idempotent: VIDs already in the list are returned in 'discarded', not an error.
    """
    total_updated = []
    total_discarded = []
    deduped = list(set(vids))

    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i : i + BATCH_SIZE]
        result = _api_post(
            f"/contacts/v1/lists/{list_id}/add",
            {"vids": batch},
            token,
        )
        total_updated.extend(result.get("updated", []))
        total_discarded.extend(result.get("discarded", []))
        if i + BATCH_SIZE < len(deduped):
            time.sleep(rate_limit_delay_s)

    return {
        "list_id": list_id,
        "submitted": len(deduped),
        "newly_added": len(total_updated),
        "already_present": len(total_discarded),
    }


def remove_from_static_list(
    list_id: int,
    vids: list[int],
    token: str,
    rate_limit_delay_s: float = 0.1,
) -> dict:
    """Remove contacts from a static list in batches."""
    total_updated = []
    total_discarded = []
    deduped = list(set(vids))

    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i : i + BATCH_SIZE]
        result = _api_post(
            f"/contacts/v1/lists/{list_id}/remove",
            {"vids": batch},
            token,
        )
        total_updated.extend(result.get("updated", []))
        total_discarded.extend(result.get("discarded", []))
        if i + BATCH_SIZE < len(deduped):
            time.sleep(rate_limit_delay_s)

    return {
        "list_id": list_id,
        "submitted": len(deduped),
        "removed": len(total_updated),
        "not_in_list": len(total_discarded),
    }


def find_and_remove_orphans(list_id: int, token: str) -> dict:
    """
    Detect contact VIDs in a static list whose contact records no longer exist,
    then remove them from the list.

    A contact is considered orphaned if HubSpot's batch read returns no result for its VID.
    """
    all_vids = list(get_all_list_vids(list_id, token))
    orphan_vids = []

    for i in range(0, len(all_vids), BATCH_SIZE):
        batch = all_vids[i : i + BATCH_SIZE]
        payload = {
            "inputs": [{"id": str(vid)} for vid in batch],
            "properties": ["lifecyclestage"],
        }
        req = urllib.request.Request(
            f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/batch/read",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
            found_ids = {int(r["id"]) for r in result.get("results", [])}
            orphan_vids.extend(v for v in batch if v not in found_ids)
        except urllib.error.HTTPError as exc:
            print(f"Batch read error at offset {i}: {exc.code}. Skipping batch.")

    if not orphan_vids:
        return {"list_id": list_id, "orphans_found": 0, "orphans_removed": 0}

    removal = remove_from_static_list(list_id, orphan_vids, token)
    return {
        "list_id": list_id,
        "total_members_before": len(all_vids),
        "orphans_found": len(orphan_vids),
        "orphans_removed": removal["removed"],
        "orphan_vids": orphan_vids,
    }
```

---

## 4. List-Membership Webhook Handler with Idempotency

### Design rationale

Three things make HubSpot webhook consumers fail in production:

1. Processing happens inside the HTTP handler, which means any downstream failure causes the consumer to return 5xx, and HubSpot never retries.
2. No deduplication — HubSpot can deliver the same event multiple times in certain edge cases (app restarts during delivery, load balancer retries on TCP errors before HubSpot reads the 200).
3. No reconciliation — the system silently diverges whenever a webhook is dropped.

This implementation separates intake (fast, always 200), processing (async, idempotent), and reconciliation (scheduled, REST-based).

```python
"""
hubspot_webhook_handler.py

Production webhook consumer for HubSpot contact.propertyChange events.

Architecture:
  HTTP handler → durable event store → async processor → reconciliation sweep

Run the HTTP server with:
  python3 -m hubspot_webhook_handler

The processor and reconciler run in background threads in this example.
In production, use a proper task queue (Celery, ARQ, SQS consumer, etc.).
"""

from __future__ import annotations
import hashlib
import hmac
import json
import sqlite3
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

HUBSPOT_CLIENT_SECRET = "load-from-env"   # os.environ["HUBSPOT_WEBHOOK_SECRET"]
HUBSPOT_API_TOKEN = "load-from-env"       # os.environ["HUBSPOT_ACCESS_TOKEN"]
DB_PATH = "/var/lib/hubspot-consumer/events.db"


# ---------------------------------------------------------------------------
# Durable event store (SQLite for single-node; replace with Postgres in prod)
# ---------------------------------------------------------------------------

def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            event_id     INTEGER PRIMARY KEY,
            received_at  REAL NOT NULL,
            processed_at REAL,
            payload      TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.commit()
    return conn


_db_conn: sqlite3.Connection | None = None
_db_lock = threading.Lock()


def get_db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is None:
        _db_conn = init_db()
    return _db_conn


def store_events(events: list[dict]) -> int:
    """
    Write raw webhook events to the durable store.
    Silently skips events whose event_id already exists (idempotent intake).
    Returns count of newly stored events.
    """
    db = get_db()
    stored = 0
    with _db_lock:
        for event in events:
            event_id = event.get("eventId")
            if event_id is None:
                continue
            try:
                db.execute(
                    "INSERT INTO webhook_events (event_id, received_at, payload) VALUES (?, ?, ?)",
                    (event_id, time.time(), json.dumps(event)),
                )
                stored += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate event_id — already stored
        db.commit()
    return stored


def fetch_pending_events(limit: int = 100) -> list[tuple[int, dict]]:
    db = get_db()
    with _db_lock:
        rows = db.execute(
            "SELECT event_id, payload FROM webhook_events WHERE status = 'pending' LIMIT ?",
            (limit,),
        ).fetchall()
    return [(row[0], json.loads(row[1])) for row in rows]


def mark_event_processed(event_id: int):
    db = get_db()
    with _db_lock:
        db.execute(
            "UPDATE webhook_events SET status = 'done', processed_at = ? WHERE event_id = ?",
            (time.time(), event_id),
        )
        db.commit()


def mark_event_failed(event_id: int, reason: str):
    db = get_db()
    with _db_lock:
        db.execute(
            "UPDATE webhook_events SET status = 'failed', processed_at = ? WHERE event_id = ?",
            (time.time(), event_id),
        )
        db.commit()


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------

def verify_v3_signature(
    method: str,
    uri: str,
    body: bytes,
    sig_header: str,
    ts_header: str,
) -> bool:
    """
    Validate HubSpot webhook signature v3.
    Rejects payloads older than 5 minutes (replay protection).
    """
    try:
        ts_ms = int(ts_header)
    except (ValueError, TypeError):
        return False
    if abs(time.time() * 1000 - ts_ms) > 300_000:
        return False  # Outside replay window
    source = f"{method}{uri}{body.decode('utf-8', errors='replace')}{ts_header}"
    expected = hmac.new(
        HUBSPOT_CLIENT_SECRET.encode(),
        source.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(sig_header, expected)


# ---------------------------------------------------------------------------
# HTTP handler — intake only, always returns 200 after storing
# ---------------------------------------------------------------------------

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        sig = self.headers.get("X-HubSpot-Signature-v3", "")
        ts = self.headers.get("X-HubSpot-Request-Timestamp", "")
        uri = self.path

        if not verify_v3_signature("POST", uri, body, sig, ts):
            self.send_response(401)
            self.end_headers()
            return

        try:
            events = json.loads(body)
            if not isinstance(events, list):
                events = [events]
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        count = store_events(events)

        # Always return 200 — never let downstream failures cause a 5xx here
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"stored": count}).encode())

    def log_message(self, format: str, *args: Any):
        pass  # Suppress default access log spam


# ---------------------------------------------------------------------------
# Async event processor — runs in background thread
# ---------------------------------------------------------------------------

def process_lifecycle_event(event: dict) -> None:
    """
    Apply the lifecycle stage change from a webhook event to local state.
    Replace this with your actual downstream logic.
    """
    contact_id = str(event.get("objectId", ""))
    new_stage = event.get("propertyValue", "")
    source = event.get("changeSource", "unknown")
    print(f"[processor] Contact {contact_id}: lifecyclestage → {new_stage} (source: {source})")
    # write to your CRM mirror, trigger nurture automation, update BI warehouse, etc.


def event_processor_loop(poll_interval_s: int = 5):
    """Background thread: drain the pending event queue and process events."""
    while True:
        pending = fetch_pending_events(limit=100)
        for event_id, event in pending:
            try:
                if event.get("propertyName") == "lifecyclestage":
                    process_lifecycle_event(event)
                # Add handlers for other subscription types here
                mark_event_processed(event_id)
            except Exception as exc:
                print(f"[processor] Failed to process event {event_id}: {exc}")
                mark_event_failed(event_id, str(exc))
        time.sleep(poll_interval_s)


# ---------------------------------------------------------------------------
# Reconciliation sweep — detects missed events
# ---------------------------------------------------------------------------

def reconcile_contacts(
    contact_ids: list[str],
    local_stage_map: dict[str, str],  # {contact_id: "customer"}
    token: str,
) -> list[dict]:
    """
    Compare local cached lifecycle stages against HubSpot's current values.
    Returns a list of divergences: contacts where local state is out of sync.
    """
    divergences = []
    for contact_id in contact_ids:
        url = (
            f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            f"?properties=lifecyclestage"
        )
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
            hs_stage = data["properties"].get("lifecyclestage", "")
            local_stage = local_stage_map.get(contact_id, "")
            if hs_stage != local_stage:
                divergences.append({
                    "contact_id": contact_id,
                    "local": local_stage,
                    "hubspot": hs_stage,
                    "action": "sync_local_to_hubspot",
                })
        except Exception as exc:
            divergences.append({
                "contact_id": contact_id,
                "error": str(exc),
            })
    return divergences


def reconciliation_loop(
    get_tracked_contacts_fn,  # callable returning {contact_id: local_stage}
    token: str,
    interval_s: int = 21600,  # every 6 hours
):
    """Background thread: periodically reconcile local state against HubSpot REST API."""
    while True:
        time.sleep(interval_s)
        local_state = get_tracked_contacts_fn()
        divergences = reconcile_contacts(list(local_state.keys()), local_state, token)
        if divergences:
            print(f"[reconciler] {len(divergences)} divergence(s) detected:")
            for d in divergences:
                print(f"  Contact {d.get('contact_id')}: local={d.get('local')!r}, hs={d.get('hubspot')!r}")
        else:
            print(f"[reconciler] State is consistent across {len(local_state)} contacts.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    # Processor thread
    processor_thread = threading.Thread(
        target=event_processor_loop,
        kwargs={"poll_interval_s": 5},
        daemon=True,
    )
    processor_thread.start()

    # HTTP server
    server = HTTPServer(("0.0.0.0", 8080), WebhookHandler)
    print("HubSpot webhook consumer listening on :8080")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
```

---

## 5. Cross-Portal List Sync

### When to use

- Agency portals that need a shared suppression list across client portals
- Staging-to-production contact mirror for testing
- Franchise networks where a central portal maintains the master suppression list and franchisee portals need a copy

### Key constraints

- Contacts are matched by email address — contacts without a matching email in the destination portal cannot be synced
- The destination list must be static — dynamic lists do not accept direct membership writes
- Rate limits apply per portal independently — the source portal and destination portal each have their own 100 calls/10s quota

```python
"""
hubspot_cross_portal_sync.py

Sync static list membership between two HubSpot portals.
Contacts are matched by email address.
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error

HUBSPOT_API_BASE = "https://api.hubapi.com"
BATCH_SIZE = 100


def get_members_with_email(list_id: int, token: str) -> list[dict]:
    """Return all list members with their email addresses."""
    members = []
    offset: int | None = None
    while True:
        url = (
            f"{HUBSPOT_API_BASE}/contacts/v1/lists/{list_id}/contacts/all"
            f"?count={BATCH_SIZE}&property=email"
        )
        if offset is not None:
            url += f"&vidOffset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        for c in data.get("contacts", []):
            email_prop = c.get("properties", {}).get("email", {})
            versions = email_prop.get("versions", [])
            email = versions[0]["value"] if versions else None
            members.append({"vid": int(c["vid"]), "email": email})
        if not data.get("has-more", False):
            break
        offset = int(data["vid-offset"])
    return members


def resolve_email_to_vid(email: str, token: str) -> int | None:
    """Look up a contact by email in a portal. Returns VID or None if not found."""
    url = f"{HUBSPOT_API_BASE}/contacts/v1/contact/email/{email}/profile"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return int(data["vid"])
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def add_vids_to_list(list_id: int, vids: list[int], token: str) -> dict:
    """Add VIDs to a static list in batches."""
    total_added = 0
    for i in range(0, len(vids), BATCH_SIZE):
        batch = vids[i : i + BATCH_SIZE]
        data = json.dumps({"vids": batch}).encode()
        req = urllib.request.Request(
            f"{HUBSPOT_API_BASE}/contacts/v1/lists/{list_id}/add",
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            total_added += len(result.get("updated", []))
        if i + BATCH_SIZE < len(vids):
            time.sleep(0.1)  # stay under 100 calls/10s
    return {"added": total_added}


def sync_list_between_portals(
    source_list_id: int,
    source_token: str,
    dest_list_id: int,
    dest_token: str,
    dry_run: bool = False,
) -> dict:
    """
    Mirror source list membership into a static list in a different HubSpot portal.

    Resolution strategy:
    - For each member in the source list, look up by email in the destination portal.
    - Members without email or without a matching contact in the destination are reported
      as unresolvable and skipped. They are not an error — they represent genuinely
      new contacts that do not yet exist in the destination portal.

    Returns a sync report.
    """
    source_members = get_members_with_email(source_list_id, source_token)
    emails = [m["email"] for m in source_members if m["email"]]

    resolved_vids: list[int] = []
    unresolvable_emails: list[str] = []
    no_email_count = len(source_members) - len(emails)

    for email in emails:
        vid = resolve_email_to_vid(email, dest_token)
        if vid is not None:
            resolved_vids.append(vid)
        else:
            unresolvable_emails.append(email)
        time.sleep(0.05)  # light rate-limit courtesy for per-email lookups

    report = {
        "source_list_id": source_list_id,
        "dest_list_id": dest_list_id,
        "source_member_count": len(source_members),
        "members_with_email": len(emails),
        "members_without_email": no_email_count,
        "resolved_in_dest": len(resolved_vids),
        "unresolvable": unresolvable_emails,
        "dry_run": dry_run,
    }

    if not dry_run and resolved_vids:
        add_result = add_vids_to_list(dest_list_id, resolved_vids, dest_token)
        report["added_to_dest"] = add_result["added"]
    else:
        report["added_to_dest"] = 0

    return report
```

### Usage

```python
import os
from hubspot_cross_portal_sync import sync_list_between_portals

SOURCE_TOKEN = os.environ["HUBSPOT_SOURCE_TOKEN"]
DEST_TOKEN = os.environ["HUBSPOT_DEST_TOKEN"]

# Dry run first — verify resolution rates before writing
report = sync_list_between_portals(
    source_list_id=42,
    source_token=SOURCE_TOKEN,
    dest_list_id=88,
    dest_token=DEST_TOKEN,
    dry_run=True,
)
print(f"Dry run: {report['resolved_in_dest']}/{report['source_member_count']} would be synced")
print(f"Unresolvable ({len(report['unresolvable'])}): {report['unresolvable'][:5]}")

# Run for real
if input("Proceed? [y/N] ").strip().lower() == "y":
    result = sync_list_between_portals(42, SOURCE_TOKEN, 88, DEST_TOKEN, dry_run=False)
    print(f"Synced {result['added_to_dest']} contacts to destination list.")
```

---

## Operational Notes

### Scheduling

| Task | Recommended cadence |
|---|---|
| Static list orphan sweep | Weekly, or 1 hour before any bulk send |
| Lifecycle reconciliation sweep | Every 6 hours |
| Cross-portal list sync (suppression) | Before every campaign send |
| Cross-portal list sync (general) | Nightly |
| Dynamic list refresh-pending audit | Immediately after any criteria change, then poll until `DONE` |

### Logging standards

Every production operation should emit structured log lines with:

- `contact_id` or `list_id`
- `action` (what was attempted)
- `result` (`applied`, `blocked`, `orphan_removed`, `divergence_detected`)
- `timestamp` (ISO 8601)
- `portal_id` (from the HubSpot token's hub ID — available at `GET /oauth/v1/access-tokens/{token}`)

### Secret handling

All tokens in these examples use `os.environ["HUBSPOT_ACCESS_TOKEN"]` and similar patterns. Never hardcode tokens. For multi-portal setups, use the credential router from `hubspot-auth` skill.

### Testing

Before running any bulk operation against a production portal:

1. Run with `dry_run=True` to see the full impact report.
2. Verify the report against your expected counts.
3. Run against a test portal or a small subset (10-20 contacts) first.
4. Keep the orphan and reconciliation sweep results in a log file for audit.
