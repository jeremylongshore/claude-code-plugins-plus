---
name: hubspot-contact-dedup
description: |
  Deduplicate HubSpot contacts at production scale — surviving import storms, wrong-winner
  merges, fuzzy-match blind spots, association orphans, rate-limit exhaustion, and silent
  merge failures on conflicting lifecycle or opt-out status. Use when cleaning a CRM after
  a bulk import, running a nightly dedup pipeline on millions of records, recovering from
  a merge that destroyed the wrong timeline, or building fuzzy matching beyond HubSpot's
  native email-uniqueness. Trigger with "hubspot dedup", "hubspot merge contacts",
  "hubspot duplicate contacts", "hubspot contact cleanup", "hubspot import duplicates",
  "hubspot fuzzy match contacts".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - crm
  - deduplication
  - data-quality
---

# HubSpot Contact Deduplication

## Overview

Merge duplicate contacts in HubSpot and operate that process in production, at scale, without data loss. This is not a one-click cleanup guide — it is the logic your pipeline runs when a sales ops team imports 80,000 leads from a tradeshow CSV that already exist in the CRM, when a merge destroys the "winner" contact's email history, when a fuzzy match on "Jon" vs "John" leaves a six-figure deal associated to a ghost record, and when on-call discovers that 40,000 contacts were merged without checking opt-out flags.

The six production failures this skill prevents:

1. **Import storms creating thousands of exact duplicates** — HubSpot enforces email uniqueness only at the property level; the merge API has no dedup-all-at-once endpoint. A 100K-row CSV import where 60% of rows already exist creates 60,000 duplicates that must be found and merged one pair at a time within a 100 req/10s rate envelope.
2. **Merge destroying the wrong timeline** — `POST /crm/v3/objects/contacts/merge` requires a `primaryObjectId`. Picking the wrong one demotes the older contact's full activity timeline — calls, emails, form submissions — to the discarded record's history.
3. **Property-based dedup missing fuzzy matches** — Email-exact dedup leaves "john@gmail.com" and "jon.smith@googlemail.com" as separate records. Phone dedup leaves "+1 (512) 867-5309" and "5128675309" as separate records. Without normalization your CRM accumulates a shadow population of semantically identical but technically distinct contacts.
4. **Post-merge association orphans** — When a secondary contact has deals, tickets, or company associations, HubSpot re-parents most automatically — but not all. Custom object associations and some third-party-integration links may not follow.
5. **Rate-limit exhaustion on large catalogs** — A 1-million-contact dedup scan requires 10,000 batch reads (2.7 hours at full throughput, before merge calls). Naive single-threaded loops exhaust the 500K daily quota before the search phase finishes.
6. **Silent merge failures on conflicting lifecycle or opt-out status** — The merge API returns 200 even when the resulting contact has `hs_email_optout=true` overriding the primary's opted-in status. HubSpot's "most recently updated value wins" rule is wrong for compliance flags.

## Auth

Authenticate with a private app token (`pat-na1-*`) or OAuth access token. Pass it on every request:

```bash
Authorization: Bearer {your-token}
```

Required scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.associations.read`, `crm.associations.write`. See the [hubspot-auth skill](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/tree/main/plugins/saas-packs/hubspot-pack/skills/hubspot-auth/SKILL.md) for token caching, OAuth refresh, and scope-drift detection.

## Prerequisites

- Python 3.10+ (`requests`, `phonenumbers`, `rapidfuzz`) for the full pipeline
- HubSpot Professional or Enterprise account (batch merge at scale)
- Private app token with required scopes (above)
- `jq` for shell examples
- For catalogs >500K contacts: confirm daily quota with HubSpot support

## Instructions

### Step 1. Discover duplicates with search

Find exact duplicates by email using the search API. Never pull all contacts into memory for comparison — use the search endpoint with specific filter values.

```bash
# Find all contacts sharing a normalized email
curl -s -X POST "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{"filters": [
      {"propertyName":"email","operator":"EQ","value":"jane.doe@example.com"}
    ]}],
    "properties": ["email","firstname","lastname","hs_object_id","createdate",
                   "lifecyclestage","hs_email_optout","hs_email_hard_bounce_reason_enum"],
    "sorts": [{"propertyName":"createdate","direction":"ASCENDING"}],
    "limit": 10
  }' | jq '[.results[] | {id, created:.properties.createdate}]'
```

For full-portal scans across millions of contacts use the four-stage Python pipeline in [implementation-guide.md](references/implementation-guide.md). The pipeline writes a local SQLite checkpoint so rate-limit interruptions do not require starting over.

### Step 2. Select the primary (winner) contact

The oldest contact by `createdate` is the primary — its timeline is most historically complete. Two overrides apply:

- If the oldest contact has `hs_email_optout=true` and the newer one does not, prefer the opted-in record as primary to avoid propagating unsubscribe status.
- If the oldest contact has a test-domain email (`@mailinator.com`, `@example.com`, `@test.com`), always make the real-address contact the primary.

```python
from datetime import datetime

def pick_primary(contacts: list[dict]) -> tuple[dict, list[dict]]:
    """Return (primary, secondaries). contacts is a list of HubSpot result dicts."""
    TEST_DOMAINS = {"mailinator.com","example.com","test.com","yopmail.com"}

    def is_test(email: str) -> bool:
        return (email or "").split("@")[-1].lower() in TEST_DOMAINS

    # Sort oldest first (default primary)
    sorted_c = sorted(contacts, key=lambda c: c["properties"]["createdate"])
    primary = sorted_c[0]

    # Opt-out override
    if primary["properties"].get("hs_email_optout") == "true":
        opted_in = next((c for c in sorted_c[1:] if c["properties"].get("hs_email_optout") != "true"), None)
        if opted_in:
            primary = opted_in

    # Test email override
    if is_test(primary["properties"].get("email", "")):
        real = next((c for c in sorted_c if not is_test(c["properties"].get("email", ""))), None)
        if real:
            primary = real

    secondaries = [c for c in contacts if c["id"] != primary["id"]]
    return primary, secondaries
```

### Step 3. Normalize emails and phones for fuzzy matching

Exact-email dedup leaves a shadow population. Normalize before comparing:

```python
import phonenumbers

def normalize_email(raw: str) -> str:
    lower = (raw or "").strip().lower().replace("@googlemail.com", "@gmail.com")
    local, _, domain = lower.partition("@")
    if domain == "gmail.com":
        local = local.split("+")[0].replace(".", "")
    return f"{local}@{domain}" if domain else lower

def normalize_phone(raw: str, region: str = "US") -> str | None:
    try:
        p = phonenumbers.parse((raw or "").strip(), region)
        if phonenumbers.is_valid_number(p):
            return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return None
```

For name similarity and the full confidence-scoring matrix, see [implementation-guide.md](references/implementation-guide.md) § Stage 2.

### Step 4. Pre-merge compliance check

Before merging, verify neither contact has blocking compliance flags:

```python
def pre_merge_check(a: dict, b: dict) -> tuple[bool, str]:
    """Returns (can_merge, reason). False = queue for human review."""
    pa, pb = a["properties"], b["properties"]
    if pa.get("hs_email_hard_bounce_reason_enum") or pb.get("hs_email_hard_bounce_reason_enum"):
        return False, "hard_bounce_present"
    # Asymmetric GDPR legal basis requires human review
    a_gdpr = bool(pa.get("hs_legal_basis"))
    b_gdpr = bool(pb.get("hs_legal_basis"))
    if a_gdpr != b_gdpr:
        return False, "gdpr_basis_asymmetry"
    return True, "ok"

# Expected post-merge opt-out: conservative — opted out if either contact is opted out
def resolve_optout(a: dict, b: dict) -> bool:
    return (a["properties"].get("hs_email_optout") == "true" or
            b["properties"].get("hs_email_optout") == "true")
```

### Step 5. Execute merge with rate limiting

```python
import time, requests

MERGE_URL = "https://api.hubapi.com/crm/v3/objects/contacts/merge"
_window_start = time.monotonic()
_window_calls = 0

def rate_gate(burst_limit: int = 90) -> None:
    """Enforce burst limit (90/10s — leaves buffer below HubSpot's 100/10s cap)."""
    global _window_start, _window_calls
    elapsed_ms = (time.monotonic() - _window_start) * 1000
    if elapsed_ms >= 10_000:
        _window_start = time.monotonic()
        _window_calls = 0
    if _window_calls >= burst_limit:
        time.sleep((10_000 - elapsed_ms) / 1000 + 0.05)
        _window_start = time.monotonic()
        _window_calls = 0
    _window_calls += 1

def merge_contacts(token: str, primary_id: str, secondary_id: str) -> bool:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for attempt in range(3):
        rate_gate()
        resp = requests.post(MERGE_URL, headers=headers,
                             json={"primaryObjectId": primary_id, "objectIdToMerge": secondary_id},
                             timeout=30)
        if resp.status_code == 200:
            return True
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", "10")))
            continue
        if resp.status_code >= 500:
            time.sleep(min(60, 5 * 2 ** attempt))
            continue
        # Non-retryable (400, 404, 409)
        print(f"Merge failed {resp.status_code}: {resp.text}")
        return False
    return False
```

Stop the pipeline before hitting the daily quota:

```python
DAILY_STOP_AT = 480_000  # Stop at 96% of 500K quota

def check_quota(resp: requests.Response) -> None:
    remaining = int(resp.headers.get("X-HubSpot-RateLimit-Daily-Remaining", 500_000))
    if (500_000 - remaining) >= DAILY_STOP_AT:
        raise SystemExit("Daily quota near limit — stopping. Resume after midnight UTC reset.")
```

### Step 6. Post-merge verification and association repair

After merging, verify that the surviving contact's `hs_email_optout` matches the expected value (Step 4) and patch it if it drifted. Then audit associations that may not have transferred automatically:

```bash
# Check associations on surviving contact (replace 12345 with actual primary contact ID)
curl -s "https://api.hubapi.com/crm/v4/objects/contacts/12345/associations/deals" \
  -H "Authorization: Bearer {your-token}" | jq '[.results[].toObjectId]'

# Manually create a missing association (replace 12345 with primary ID, 67890 with deal ID)
curl -s -X PUT \
  "https://api.hubapi.com/crm/v4/objects/contacts/12345/associations/deals/67890" \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '[{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":3}]'
```

The full four-stage Python pipeline (scan → pair → qualify → execute) with automatic association repair is in [implementation-guide.md](references/implementation-guide.md).

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `400` | `CONTACT_ALREADY_MERGED` | Secondary was already merged into another record | Re-fetch secondary; check `hs_merged_object_ids` for surviving primary ID |
| `400` | `SAME_OBJECT_MERGE` | Both IDs are identical | Remove self-merge pairs from candidate list before executing |
| `400` | `INVALID_OBJECT_TYPE` | One ID belongs to a different CRM object type | Verify via `GET /crm/v3/objects/contacts/{id}` before merging |
| `404` | `OBJECT_NOT_FOUND` | Contact was deleted between discovery and merge | Re-fetch to confirm existence; skip if deleted |
| `409` | `MERGE_IN_PROGRESS` | A concurrent merge is already running for this contact | Retry after 30 seconds |
| `429` | Rate limit | Burst or daily quota exceeded | Honor `Retry-After` header; check `X-HubSpot-RateLimit-Daily-Remaining` |
| `500` | `INTERNAL_ERROR` | Transient HubSpot platform fault | Exponential back-off, max 3 retries; log `X-HubSpot-Correlation-Id` for support |
| `200` (silent) | Opt-out propagated incorrectly | "Most recently updated wins" resolved compliance flag wrong | Run post-merge `hs_email_optout` verification; patch via PATCH endpoint |

## Examples

### Merge two contacts via curl

```bash
# Step 1: find the duplicate pair sorted oldest-first
SEARCH=$(curl -s -X POST "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer {your-token}" -H "Content-Type: application/json" \
  -d '{"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":"jane.doe@example.com"}]}],
       "properties":["email","createdate"],"sorts":[{"propertyName":"createdate","direction":"ASCENDING"}],"limit":5}')

PRIMARY_ID=$(echo "$SEARCH" | jq -r '.results[0].id')
SECONDARY_ID=$(echo "$SEARCH" | jq -r '.results[1].id')
echo "primary=$PRIMARY_ID secondary=$SECONDARY_ID"

# Step 2: merge
curl -s -X POST "https://api.hubapi.com/crm/v3/objects/contacts/merge" \
  -H "Authorization: Bearer {your-token}" -H "Content-Type: application/json" \
  -d "{\"primaryObjectId\":\"$PRIMARY_ID\",\"objectIdToMerge\":\"$SECONDARY_ID\"}" \
  | jq '{id, email: .properties.email}'
```

### Dry-run dedup report

```bash
python3 - <<'EOF'
import json, subprocess, sys

TOKEN = "{your-token}"
EMAIL = "jane.doe@example.com"

out = subprocess.run([
    "curl","-s","-X","POST","https://api.hubapi.com/crm/v3/objects/contacts/search",
    "-H",f"Authorization: Bearer {TOKEN}","-H","Content-Type: application/json",
    "-d", json.dumps({"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":EMAIL}]}],
                      "properties":["email","firstname","lastname","createdate","lifecyclestage"],
                      "sorts":[{"propertyName":"createdate","direction":"ASCENDING"}],"limit":10}),
], capture_output=True, text=True).stdout

data = json.loads(out)
contacts = data["results"]
if len(contacts) < 2:
    print("No duplicates found"); sys.exit(0)
print(f"Found {len(contacts)} contacts for {EMAIL}:")
for c in contacts:
    p = c["properties"]
    print(f"  ID {c['id']} | created {p['createdate']} | stage {p.get('lifecyclestage')}")
print(f"\nWould merge: primary={contacts[0]['id']}, secondaries={[c['id'] for c in contacts[1:]]}")
EOF
```

### Batch read to pre-fetch properties before deciding primary

```bash
curl -s -X POST "https://api.hubapi.com/crm/v3/objects/contacts/batch/read" \
  -H "Authorization: Bearer {your-token}" -H "Content-Type: application/json" \
  -d '{
    "inputs": [{"id":"101"},{"id":"202"},{"id":"303"}],
    "properties": ["email","phone","firstname","lastname","createdate",
                   "lifecyclestage","hs_email_optout","hs_email_hard_bounce_reason_enum"]
  }' | jq '[.results[] | {id, email:.properties.email, created:.properties.createdate}]'
```

## Output

- Candidate list grouped by normalized email, phone, or name similarity with confidence scores
- Winner selection rationale per merge pair (oldest contact, opt-out override, test-email override)
- Compliance pre-check table per pair (opt-out status, lifecycle, GDPR basis, hard-bounce flag)
- Association audit report — which transferred automatically and which required manual re-parenting
- Merge execution log with rate-limit headers and daily quota burn rate
- Post-merge verification confirming `hs_email_optout` on surviving records matches expected value
- Human review queue for pairs flagged with conflicting compliance flags or 0.70–0.84 confidence

## Resources

- [HubSpot Contacts Merge API](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts#merge-contacts)
- [CRM Search API Reference](https://developers.hubspot.com/docs/guides/api/crm/search)
- [CRM Batch Read API](https://developers.hubspot.com/docs/reference/api/crm/objects/contacts#post-%2Fcrm%2Fv3%2Fobjects%2Fcontacts%2Fbatch%2Fread)
- [Associations API v4](https://developers.hubspot.com/docs/guides/api/crm/associations/associations-v4)
- [Rate Limits Reference](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- GDPR and Marketing Emails in HubSpot
- [API_REFERENCE.md](references/API_REFERENCE.md) — merge endpoint shapes, search filter syntax, error codes, property uniqueness enforcement
- [implementation-guide.md](references/implementation-guide.md) — full four-stage Python pipeline, fuzzy matching, post-merge association cleanup runbook
