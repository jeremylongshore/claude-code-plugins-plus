---
name: hubspot-lifecycle-and-lists
description: |
  Manage HubSpot lifecycle stages and list segmentation in production without
  silently destroying CRM trust. Covers lifecycle stage progression guards that
  prevent regression, dynamic list criteria drift, static list orphan detection,
  lead-scoring source-of-truth conflicts, webhook-missed-event recovery, and
  cross-portal list sync. Use when moving contacts through the funnel, building
  segment-based nurture flows, auditing list membership integrity, reconciling
  external lead scores with HubSpot native scoring, or standing up a webhook
  consumer that must never lose a membership-change event. Trigger with "hubspot
  lifecycle", "hubspot list segmentation", "hubspot dynamic list", "hubspot static
  list", "hubspot lead scoring conflict", "lifecycle regression", "list membership
  webhook", "cross-portal list sync".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(python3:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - lifecycle
  - segmentation
  - marketing-ops
---

# HubSpot Lifecycle and Lists

## Overview

Move contacts through the HubSpot funnel and maintain list integrity in a production system. This is not a setup walkthrough — it is the code your marketing-ops integration runs when a lifecycle stage update would silently regress a Customer back to Subscriber, when a dynamic list's criteria change orphans members who qualified last week, when a static list import references contacts that were deleted from the portal, when an external lead-scoring model creates a second source of truth that fights HubSpot's native scoring, when a list-membership webhook fires but your consumer returns 5xx and HubSpot never retries, and when an agency needs to mirror list membership across two portals that have no native sync API.

The six production failures this skill prevents:

1. **Lifecycle stage regression** — HubSpot's `PATCH /crm/v3/objects/contacts/{id}` will set lifecyclestage to any valid value regardless of direction. Setting a Customer back to Subscriber silently destroys funnel attribution, invalidates reporting, and corrupts revenue forecasting. The API returns `200 OK`. There is no built-in guard.
2. **Dynamic list criteria drift** — editing a dynamic list's filter criteria does not immediately re-evaluate existing members against the new rules. Members who no longer qualify remain in the list until the nightly background refresh completes, creating a stale membership window of up to 24 hours that can trigger incorrect nurture emails or suppression failures.
3. **Static list import orphans** — contacts added to a static list via import or `POST /contacts/v1/lists/{listId}/add` remain list members even after the underlying contact record is hard-deleted from the CRM. These orphan IDs return errors on any subsequent contact-level API call and pollute downstream sync pipelines.
4. **Lead scoring model disagreement** — writing an external score to a custom contact property while HubSpot's native Lead Scoring tool computes its own score creates two competing signals. Sales works from the HubSpot Score field; marketing automation triggers on the custom property. The two scores diverge and nobody knows which one to trust.
5. **List-membership webhook missed events** — HubSpot's webhook system delivers `contact.propertyChange` events for lifecyclestage updates and list-membership changes via HTTP POST with no retry on 5xx responses. A single downstream outage during a bulk-import window can drop hundreds of membership events permanently with no dead-letter queue or re-delivery mechanism.
6. **Cross-portal list sync** — agencies managing multiple HubSpot portals (e.g., a staging portal mirroring a production portal, or two franchisee portals needing shared suppression lists) have no native API to sync list membership between portals. Manual export-import lags by hours and has no idempotency guarantee.

## Prerequisites

- HubSpot account with a private app token scoped to:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.lists.read`
  - `crm.lists.write`
  - `crm.schemas.contacts.read` (for lifecycle stage enumeration)
- Python 3.10+ or Node.js 18+ for implementation examples
- `jq` on PATH for shell-level inspection
- `curl` for API verification steps
- For webhook consumption: an HTTPS endpoint reachable by HubSpot's webhook delivery infrastructure
- For cross-portal sync: private app tokens for both portals stored in separate environment variables or a credential router (see `hubspot-auth` skill)

Store all tokens in a secret manager. Never put `pat-na1-*` values in source code or committed `.env` files.

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Lifecycle stage progression guard (neutralizes regression)

The lifecycle stage enum has a defined forward direction. Any update that moves a contact backward is almost certainly a data pipeline bug, not an intentional business action.

Canonical stage order (HubSpot internal values, not display labels):

```
subscriber → lead → marketingqualifiedlead → salesqualifiedlead → opportunity → customer → evangelist → other
```

`other` is a lateral bucket, not a terminal stage — it sits outside the linear progression and should only be set explicitly.

Never read the stage order from display labels. Display labels are portal-configurable. Always use the internal enum values.

**Progression guard pattern (Python):**

```python
STAGE_ORDER = [
    "subscriber",
    "lead",
    "marketingqualifiedlead",
    "salesqualifiedlead",
    "opportunity",
    "customer",
    "evangelist",
]
# 'other' is not in the linear sequence — treat as a lateral assignment

def stage_index(stage: str) -> int:
    try:
        return STAGE_ORDER.index(stage.lower())
    except ValueError:
        return -1  # 'other' or unknown — always allow

def safe_set_lifecycle(contact_id: str, new_stage: str, token: str) -> dict:
    current = get_contact_lifecycle(contact_id, token)
    current_idx = stage_index(current)
    new_idx = stage_index(new_stage)

    # Allow lateral 'other' assignments and forward progressions
    if current_idx != -1 and new_idx != -1 and new_idx < current_idx:
        raise ValueError(
            f"Lifecycle regression blocked: {current} → {new_stage} "
            f"for contact {contact_id}. "
            f"Current index={current_idx}, requested index={new_idx}."
        )

    return patch_contact_lifecycle(contact_id, new_stage, token)

def get_contact_lifecycle(contact_id: str, token: str) -> str:
    import urllib.request, json
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}?properties=lifecyclestage"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["properties"].get("lifecyclestage", "subscriber")

def patch_contact_lifecycle(contact_id: str, stage: str, token: str) -> dict:
    import urllib.request, json
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    payload = json.dumps({"properties": {"lifecyclestage": stage}}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

Verify a contact's current stage before running a bulk update:

```bash
curl -s \
  "https://api.hubapi.com/crm/v3/objects/contacts/{contact-id}?properties=lifecyclestage" \
  -H "Authorization: Bearer {your-token}" \
  | jq '.properties.lifecyclestage'
```

### 2. Dynamic list criteria drift (neutralizes stale membership)

When you edit a dynamic list's filter criteria, HubSpot queues a background re-evaluation job. Existing members who no longer satisfy the new criteria remain in the list until that job completes — up to 24 hours. Any automation triggered on list membership during that window operates on stale data.

**Production pattern: snapshot membership before and after a criteria change, then audit the delta.**

```python
import urllib.request, json, time

def snapshot_list_members(list_id: int, token: str) -> set[str]:
    """Return the full set of vid (legacy contact ID) strings for a list."""
    vids = set()
    offset = None
    while True:
        url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all?count=100"
        if offset:
            url += f"&vidOffset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        for contact in data.get("contacts", []):
            vids.add(str(contact["vid"]))
        if not data.get("has-more", False):
            break
        offset = data["vid-offset"]
    return vids

def audit_criteria_drift(list_id: int, token: str, poll_interval_s: int = 3600):
    """
    Take a pre-criteria-change snapshot, wait for the nightly refresh window,
    take a post snapshot, and report contacts that should have been removed.
    Call this before editing criteria and again after the refresh window.
    """
    before = snapshot_list_members(list_id, token)
    print(f"Pre-change member count: {len(before)}")
    print(f"Snapshot saved. Re-run after {poll_interval_s}s (or after nightly refresh).")
    return before
```

**Shell verification of list metadata:**

```bash
curl -s \
  "https://api.hubapi.com/contacts/v1/lists/{list-id}" \
  -H "Authorization: Bearer {your-token}" \
  | jq '{listId, name, listType, updatedAt, metaData}'
```

Flag the list as `DYNAMIC` in your internal registry and mark it "refresh-pending" whenever criteria change. Suppress automation triggers until a post-refresh snapshot confirms membership is stable.

### 3. Static list orphan detection (neutralizes orphan IDs)

A static list retains member IDs after the underlying contact record is hard-deleted. Batch-processing that list later will hit `404` on every orphaned ID, burning API quota and producing false error telemetry.

**Orphan sweep pattern (key logic):**

```python
def find_orphaned_members(list_id: int, token: str, batch_size: int = 100) -> list[str]:
    """Return vids in the list whose contact records no longer exist."""
    all_vids = list(snapshot_list_members(list_id, token))
    orphans = []
    for i in range(0, len(all_vids), batch_size):
        batch = all_vids[i : i + batch_size]
        payload = json.dumps({
            "inputs": [{"id": vid} for vid in batch],
            "properties": ["lifecyclestage"],
        }).encode()
        # POST /crm/v3/objects/contacts/batch/read
        # Any VIDs absent from results[] are orphaned
        result = batch_read_contacts(payload, token)
        found_ids = {str(r["id"]) for r in result.get("results", [])}
        orphans.extend(v for v in batch if v not in found_ids)
    return orphans
```

Full `batch_read_contacts` + `remove_orphans_from_static_list` implementations: [implementation-guide.md](references/implementation-guide.md) § Static List Batch Membership Manager.

Schedule this sweep weekly and before any bulk send that reads the static list.

### 4. Lead scoring source-of-truth resolution (neutralizes scoring conflict)

If HubSpot's native Lead Scoring tool is active on a portal, it writes to the system-managed `hs_lead_status` and `hubspotscore` properties. Writing an external score to `hubspotscore` directly is blocked — HubSpot rejects the PATCH with a `400`. Writing to a custom property (e.g., `external_lead_score`) creates a second source of truth that sales and marketing will each discover separately and use inconsistently.

**Resolution pattern — pick one authority and route everything through it:**

Option A (HubSpot is authority): disable or remove the HubSpot native scoring ruleset, write the external score to `hubspotscore` via the API, and document the source in the portal's settings notes.

Option B (external model is authority): disable native HubSpot scoring, write the external score to a single custom property (`external_lead_score`), and update every automation and workflow filter to reference that property instead of `hubspotscore`. Write a clear comment in every HubSpot workflow that `hubspotscore` is not used.

Option C (both must coexist): keep both, but surface the discrepancy to the rep via a third computed field:

```python
def write_external_score(contact_id: str, score: int, token: str):
    """
    Write external score to a custom property. Never write to hubspotscore
    if HubSpot native scoring is active — the PATCH will be rejected.
    """
    payload = json.dumps({"properties": {"external_lead_score": str(score)}}).encode()
    req = urllib.request.Request(
        f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

Document the scoring authority in a pinned internal wiki page. Ambiguity here compounds over time.

### 5. Webhook missed-event recovery (neutralizes delivery gaps)

HubSpot delivers `contact.propertyChange` events (for `lifecyclestage`) and list-membership events via HTTP POST to your registered endpoint. If your consumer returns a 5xx, HubSpot does not retry. There is no dead-letter queue, no re-delivery, no backfill API. The event is permanently lost.

**Three-layer defense:**

**Layer 1 — Fast consumer with async processing.** Accept the POST, validate the signature, write the raw payload to a durable queue (Redis, SQS, Postgres `events` table), return `200` immediately. Never do downstream processing inside the HTTP handler — any exception there causes a 5xx and the event is lost.

**Layer 2 — Idempotent event processor.** Use the HubSpot `eventId` as an idempotency key before processing:

```python
PROCESSED_EVENT_IDS = set()  # replace with Redis SET or DB unique constraint

def process_event(event: dict):
    event_id = event.get("eventId")
    if event_id in PROCESSED_EVENT_IDS:
        return  # duplicate delivery — skip
    PROCESSED_EVENT_IDS.add(event_id)
    # downstream logic here — never inside the HTTP handler
```

**Layer 3 — Reconciliation sweep.** Every 6 hours, compare local cached lifecycle stages to the HubSpot REST API. Divergence = missed webhook.

Full HTTP handler with SQLite durable store, v3 signature validation, processor thread, and reconciliation loop: [implementation-guide.md](references/implementation-guide.md) § List-Membership Webhook Handler with Idempotency.

### 6. Cross-portal list sync (neutralizes agency-sync gap)

There is no HubSpot API endpoint for "sync list A in portal X to list B in portal Y." The workaround is a two-leg pull-and-push:

1. Paginate `GET /contacts/v1/lists/{sourceListId}/contacts/all?property=email` from the source portal to collect all member emails.
2. Resolve each email to a contact VID in the destination portal via `GET /contacts/v1/contact/email/{email}/profile`. Contacts with no matching email in the destination are unresolvable — log and skip, do not fail the sync.
3. Write resolved VIDs to the destination static list via `POST /contacts/v1/lists/{destListId}/add` in batches of 100.

Key constraint: the destination list must be `STATIC` — dynamic lists reject direct membership writes.

Full implementation with dry-run mode, unresolvable reporting, and rate-limit delays: [implementation-guide.md](references/implementation-guide.md) § Cross-Portal List Sync.

Schedule this sync as a nightly job. For suppression lists, run it before every campaign send, not on a calendar cadence.

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `400 BAD_REQUEST` | `PROPERTY_VALUE_NOT_FOUND` | Invalid lifecycle stage enum value sent in PATCH | Validate against canonical enum before calling — see API_REFERENCE.md lifecycle stage table |
| `400 BAD_REQUEST` | `Cannot modify system-managed property` | Attempt to write to `hubspotscore` while native scoring is active | Disable native scoring or write to a custom property instead |
| `404 NOT_FOUND` | Contact not found | Orphaned VID in a static list, or contact was hard-deleted | Run orphan sweep, remove VID from list |
| `404 NOT_FOUND` | List not found | List was deleted; IDs are not reused | Remove the list reference from all automation configs |
| `409 CONFLICT` | `CONTACT_ALREADY_EXISTS_IN_LIST` | Duplicate add to a static list | Idempotent — treat as success, not error |
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | API quota exhausted (100 calls/10s per private app) | Back off with `Retry-After` header; use batch endpoints to reduce call count |
| `500 INTERNAL_SERVER_ERROR` | HubSpot internal error | Transient HubSpot infrastructure issue | Retry with exponential backoff (max 4 attempts); log for rate-limit awareness |
| `0` (no response) | Webhook delivery failed | Your consumer returned 5xx or timed out | HubSpot will not retry — rely on reconciliation sweep to detect and correct |

## Examples

### Set a contact's lifecycle stage forward

```bash
curl -s -X PATCH \
  "https://api.hubapi.com/crm/v3/objects/contacts/{contact-id}" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"lifecyclestage": "salesqualifiedlead"}}' \
  | jq '{id, properties: {lifecyclestage: .properties.lifecyclestage}}'
```

### Search for all Customers

```bash
curl -s -X POST \
  "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{"filters": [{"propertyName": "lifecyclestage", "operator": "EQ", "value": "customer"}]}],
    "properties": ["email", "lifecyclestage", "hs_lead_status"],
    "limit": 100
  }' \
  | jq '{total, results: [.results[] | {id, email: .properties.email, stage: .properties.lifecyclestage}]}'
```

### Create a static list

```bash
curl -s -X POST \
  "https://api.hubapi.com/contacts/v1/lists" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "2026-Q2 Campaign — Suppression", "dynamic": false}' \
  | jq '{listId, name, listType}'
```

### Add contacts to a static list

```bash
curl -s -X POST \
  "https://api.hubapi.com/contacts/v1/lists/{list-id}/add" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{"vids": [12345, 67890, 11223]}' \
  | jq '{updated, discarded}'
```

### List all lists for a portal

```bash
curl -s \
  "https://api.hubapi.com/contacts/v1/lists/all/lists/static?count=250" \
  -H "Authorization: Bearer {your-token}" \
  | jq '[.lists[] | {listId, name, updatedAt, metaData: {size: .metaData.size}}]'
```

### Run a lifecycle stage bulk update with progression guard

```bash
python3 - <<'EOF'
import os, json
# Load the progression-guard code from implementation-guide.md
# Then run a dry-run report before committing changes
contacts = [
    {"id": "12345", "target_stage": "marketingqualifiedlead"},
    {"id": "67890", "target_stage": "customer"},
]
token = os.environ["HUBSPOT_ACCESS_TOKEN"]
for c in contacts:
    try:
        result = safe_set_lifecycle(c["id"], c["target_stage"], token)
        print(f"Updated {c['id']} → {c['target_stage']}")
    except ValueError as e:
        print(f"BLOCKED: {e}")
EOF
```

## Output

- Lifecycle stage progression guard that blocks regressions before the API call is made
- Dynamic list criteria drift audit with pre/post membership snapshots
- Static list orphan sweep that identifies and removes deleted-contact VIDs
- Lead scoring single-source-of-truth decision record (option A/B/C documented)
- Webhook consumer with durable queue intake, signature validation, and idempotency key deduplication
- Reconciliation sweep comparing local state to HubSpot REST API for divergence detection
- Cross-portal list sync with email-based contact resolution and unresolvable contact reporting

## Resources

- [HubSpot CRM Contacts API v3](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts)
- [Contacts Lists API v1](https://developers.hubspot.com/docs/reference/api/marketing/lists/legacy-v1-lists)
- [Lifecycle Stage Property Reference](https://knowledge.hubspot.com/contacts/use-lifecycle-stages)
- [HubSpot Webhooks Documentation](https://developers.hubspot.com/docs/guides/apps/webhooks/overview)
- [Webhook Signature Validation](https://developers.hubspot.com/docs/guides/apps/webhooks/validating-requests)
- [CRM Search API](https://developers.hubspot.com/docs/guides/api/crm/search)
- [Batch Contact Operations](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts#batch-operations)
- Lead Scoring in HubSpot
- [API_REFERENCE.md](references/API_REFERENCE.md) — lifecycle stage enum, list API endpoint shapes, webhook event schemas, filter syntax
- [implementation-guide.md](references/implementation-guide.md) — lifecycle progression guard, dynamic list criteria builder, static list batch management, webhook handler with idempotency
