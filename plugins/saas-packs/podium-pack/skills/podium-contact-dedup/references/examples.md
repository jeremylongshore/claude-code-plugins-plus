# Examples — podium-contact-dedup

Ten complete worked examples. Each is runnable end-to-end with the env vars and inputs listed at the top of the snippet.

## 1. Normalize one phone from the CLI

```bash
python3 scripts/phone_normalize.py --phone "0412 345 678" --region AU --output json
```

Output:

```json
{
  "valid": true,
  "e164": "+61412345678",
  "national": "0412 345 678",
  "country": "AU",
  "natural_key": "+61412345678"
}
```

Same phone in four different input formats, all produce the same `natural_key`:

```bash
for raw in "+61 412 345 678" "0412 345 678" "(04) 1234-5678" "+61412345678"; do
  python3 scripts/phone_normalize.py --phone "$raw" --region AU --output json | jq -c '{input: "'"$raw"'", key: .natural_key}'
done
```

Output:

```json
{"input":"+61 412 345 678","key":"+61412345678"}
{"input":"0412 345 678","key":"+61412345678"}
{"input":"(04) 1234-5678","key":"+61412345678"}
{"input":"+61412345678","key":"+61412345678"}
```

## 2. Build the natural-key index for a location

```bash
# env: PODIUM_ACCESS_TOKEN (from podium-auth)
python3 scripts/find_duplicates.py \
  --location-uid loc_abc123 \
  --db ./podium-dedup.sqlite \
  --token-env PODIUM_ACCESS_TOKEN \
  --region AU \
  --output json > clusters.json
```

The script pages through `GET /v4/contacts?location_uid=loc_abc123`, normalizes every phone, upserts into the SQLite index, then emits cluster proposals to stdout.

Inspect the index after the run:

```bash
sqlite3 ./podium-dedup.sqlite \
  "SELECT natural_key, COUNT(*) AS dupes FROM contact_index GROUP BY natural_key HAVING dupes >= 2 LIMIT 10;"
```

## 3. Read a cluster proposal

`clusters.json` (one cluster per object, NDJSON):

```json
{
  "cluster_id": "cl_7f3a9c1d",
  "natural_key": "+61400000000",
  "confidence": 0.95,
  "auto_merge": true,
  "suggested_primary_uid": "ct_alpha111",
  "members": [
    {"contact_uid": "ct_alpha111", "field_count": 12, "updated_at": "2026-05-10T08:00:00Z", "marketing_opt_out": false},
    {"contact_uid": "ct_alpha222", "field_count":  7, "updated_at": "2026-05-08T14:00:00Z", "marketing_opt_out": true},
    {"contact_uid": "ct_alpha333", "field_count":  4, "updated_at": "2026-05-09T10:00:00Z", "marketing_opt_out": false}
  ]
}
```

Note: `ct_alpha111` is suggested primary (highest field_count). `ct_alpha222` has `marketing_opt_out=true` — the union policy will force the merged record to have `marketing_opt_out=true`.

## 4. Dry-run a merge

```bash
python3 scripts/merge_contacts.py \
  --cluster-id cl_7f3a9c1d \
  --db ./podium-dedup.sqlite \
  --token-env PODIUM_ACCESS_TOKEN \
  --dry-run
```

Output:

```json
{
  "cluster_id": "cl_7f3a9c1d",
  "would_merge": {
    "primary_uid": "ct_alpha111",
    "duplicate_uids": ["ct_alpha222", "ct_alpha333"],
    "opt_out_union": {
      "marketing_opt_out": true,
      "sms_opt_out":       false,
      "email_opt_out":     false
    },
    "api_calls": [
      "GET /v4/contacts/ct_alpha222   (conflict check)",
      "GET /v4/contacts/ct_alpha333   (conflict check)",
      "POST /v4/contacts/ct_alpha111/merge {\"duplicate_uids\": [\"ct_alpha222\", \"ct_alpha333\"]}",
      "PATCH /v4/contacts/ct_alpha111 {\"marketing_opt_out\": true, \"sms_opt_out\": false, \"email_opt_out\": false}"
    ]
  },
  "would_not_call_podium": true
}
```

## 5. Execute the merge for real

```bash
python3 scripts/merge_contacts.py \
  --cluster-id cl_7f3a9c1d \
  --db ./podium-dedup.sqlite \
  --token-env PODIUM_ACCESS_TOKEN
```

Exit code 0 with a final audit-log entry:

```json
{
  "ts": "2026-05-12T16:00:01Z",
  "event": "merge_complete",
  "cluster_id": "cl_7f3a9c1d",
  "primary_uid": "ct_alpha111",
  "duplicate_uids": ["ct_alpha222", "ct_alpha333"],
  "opt_out_pre_merge": {
    "ct_alpha111": {"marketing_opt_out": false, "sms_opt_out": false, "email_opt_out": false},
    "ct_alpha222": {"marketing_opt_out": true,  "sms_opt_out": false, "email_opt_out": false},
    "ct_alpha333": {"marketing_opt_out": false, "sms_opt_out": false, "email_opt_out": false}
  },
  "opt_out_post_merge": {"marketing_opt_out": true, "sms_opt_out": false, "email_opt_out": false},
  "soft_delete": true,
  "restorable": true
}
```

## 6. Batch-merge all auto-merge clusters

```bash
jq -c 'select(.auto_merge == true) | .cluster_id' clusters.json | while read -r cid; do
  python3 scripts/merge_contacts.py --cluster-id "$cid" \
    --db ./podium-dedup.sqlite \
    --token-env PODIUM_ACCESS_TOKEN || echo "FAILED: $cid"
done
```

Each cluster goes through the full state machine (`pending → merging → merged → patched`) independently. Failures do not block the queue.

## 7. Cross-location dedup scan

```bash
# Run after per-location dedup completes for every location_uid in the tenant.
python3 scripts/cross_location_dedup.py \
  --db ./podium-dedup.sqlite \
  --output cross-location-review.json
```

Output (NDJSON, one cluster per line):

```json
{
  "natural_key": "+61400000000",
  "members": [
    {"contact_uid": "ct_sydney111", "location_uid": "loc_sydney"},
    {"contact_uid": "ct_burleigh222", "location_uid": "loc_burleigh_heads"}
  ],
  "policy": "review",
  "reason": "cross_location_merge_default_off_pending_operator_review"
}
```

This file is meant for human review — neither the script nor anything downstream auto-merges these without an explicit per-tenant policy change.

## 8. Resume after crash

```bash
# A previous merge run crashed at 80%. The merge_state table has rows
# in pending / merging / merged states (non-terminal).
sqlite3 ./podium-dedup.sqlite \
  "SELECT status, COUNT(*) FROM merge_state GROUP BY status;"
```

Output:

```
patched|1487
merging|3
pending|12
```

Just re-run the merge script — the resume path picks up non-terminal rows:

```bash
python3 scripts/merge_contacts.py --resume --db ./podium-dedup.sqlite --token-env PODIUM_ACCESS_TOKEN
```

For each non-terminal row, the orchestrator GETs the primary from Podium, sees whether the merge already completed (status=`merged` → run PATCH; status=`patched` → done), and reconciles.

## 9. Inspect the audit log for compliance

```bash
# Every merge entry records pre- and post-merge opt-out state.
jq 'select(.event == "merge_complete" and (.opt_out_pre_merge | to_entries[] | .value.marketing_opt_out == true))' \
  audit-log.jsonl | head -3
```

Output filtered to merges where at least one duplicate had `marketing_opt_out=true`. Verify every such merge ends with `opt_out_post_merge.marketing_opt_out == true`. If any does not, escalate to compliance.

## 10. Pre-write dedup check from a consumer skill (webchat-handler)

```python
# When a webchat message arrives with a phone, check the dedup index BEFORE
# creating a new Podium contact. Prevents new duplicates at write time.
import sqlite3
import sys
sys.path.insert(0, "../podium-contact-dedup/scripts")
from phone_normalize import normalize_phone

def find_existing_contact(db_path: str, raw_phone: str, region: str = "AU") -> dict | None:
    norm = normalize_phone(raw_phone, default_region=region)
    if not norm["valid"]:
        return None
    db = sqlite3.connect(db_path)
    row = db.execute(
        "SELECT contact_uid, location_uid, name FROM contact_index "
        "WHERE natural_key = ? AND deleted_at_podium IS NULL "
        "ORDER BY field_count DESC LIMIT 1",
        (norm["natural_key"],),
    ).fetchone()
    db.close()
    if row:
        return {"contact_uid": row[0], "location_uid": row[1], "name": row[2]}
    return None

# Usage in podium-webchat-handler
existing = find_existing_contact("./podium-dedup.sqlite", "0412 345 678")
if existing:
    contact_uid = existing["contact_uid"]   # reuse it
else:
    contact_uid = create_new_contact(...)   # fall through to create-new path
```

The natural-key index is the cheapest possible lookup — sub-millisecond — and prevents the most expensive operation (a downstream merge run cleaning up the duplicate this write would otherwise have created).
