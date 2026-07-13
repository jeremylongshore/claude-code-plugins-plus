# Examples — podium-multi-location-router

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal two-location dispatch (Python, async)

```python
# env: PODIUM_LOCATION_CREDENTIALS (path to credentials map)
import asyncio
from location_router import LocationRouter

async def main():
    router = LocationRouter.from_credentials_file(
        "./config/locations.json",
        audit_log_path="./audit-log/podium-router.jsonl",
    )

    # KombiLife Sydney — write a contact
    sydney = router.get_client(location_uid="loc_placeholder_001")
    r = await sydney.call("POST", "/v4/contacts", json={
        "first_name": "Jane", "last_name": "Doe",
        "phone": "+15555550100",
        "location_uid": "loc_placeholder_001",
    })
    r.raise_for_status()

    # KombiLife Burleigh Heads — independent of Sydney's auth + bucket
    burleigh = router.get_client(location_uid="loc_placeholder_002")
    r2 = await burleigh.call("GET", "/v4/conversations?location_uid=loc_placeholder_002")
    r2.raise_for_status()

asyncio.run(main())
```

Two writes, two distinct audit-log lines, two independent rate-limit buckets, two independent auth instances. The router enforces the separation; the application code never has to think about it.

## 2. Credentials-map file format

```json
{
  "loc_placeholder_001": {
    "org_slug": "kombilife",
    "client_id": "{your-client-id}",
    "client_secret": "{your-client-secret}",
    "refresh_token_file": "./secrets/sydney-refresh.json"
  },
  "loc_placeholder_002": {
    "org_slug": "kombilife",
    "client_id": "{your-client-id}",
    "client_secret": "{your-client-secret}",
    "refresh_token_file": "./secrets/burleigh-refresh.json"
  }
}
```

Same `client_id` / `client_secret` because both locations live under one OAuth app at the org level. Distinct `refresh_token_file` paths because the router treats them as independent routing keys. File mode `0600`; never commit unencrypted.

## 3. Pre-flight verify a location_uid

```bash
# Confirm the credentials for loc_placeholder_001 actually own that location.
python3 scripts/verify_location.py \
  --location-uid loc_placeholder_001 \
  --credentials-file ./config/locations.json
```

Output:

```json
{
  "location_uid": "loc_placeholder_001",
  "status": "in_scope",
  "scope_size": 2,
  "verified_at": 1715515200.0
}
```

Exit code 0 = in scope; exit code 1 = not in scope (silent 403 prevented); exit code 2 = config or network error.

## 4. Onboard a new location idempotently

```bash
# First run — onboards the location.
python3 scripts/onboard_location.py \
  --location-uid {your-new-location-uid} \
  --org-slug kombilife \
  --client-id-env PODIUM_CLIENT_ID \
  --client-secret-env PODIUM_CLIENT_SECRET \
  --refresh-token-file ./secrets/new-store-refresh.json \
  --credentials-file ./config/locations.json
# → status: onboarded

# Second run with the same input — idempotent, no duplication.
python3 scripts/onboard_location.py \
  --location-uid {your-new-location-uid} \
  ...
# → status: skipped_existing
```

The script writes the new entry atomically (temp file + rename), builds the `PodiumAuth` instance, calls `GET /v4/locations` to verify the credential actually owns the new UID, and only on full success commits the entry to the live map.

## 5. Bulk onboard 5 locations — recover from partial failure

```python
# env: PODIUM_LOCATION_CREDENTIALS, PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET
import asyncio
from location_router import LocationRouter, LocationCredential

async def main():
    router = LocationRouter.from_credentials_file("./config/locations.json",
                                                  audit_log_path="./audit-log/podium-router.jsonl")

    new = [
        LocationCredential("loc_placeholder_010", "agency-client-1", "{cid}", "{csec}", "./secrets/c1-l1.json"),
        LocationCredential("loc_placeholder_011", "agency-client-1", "{cid}", "{csec}", "./secrets/c1-l2.json"),
        LocationCredential("loc_placeholder_012", "agency-client-2", "{cid}", "{csec}", "./secrets/c2-l1.json"),
        LocationCredential("loc_placeholder_013", "agency-client-2", "{cid}", "{csec}", "./secrets/c2-l2.json"),
        LocationCredential("loc_placeholder_014", "agency-client-3", "{cid}", "{csec}", "./secrets/c3-l1.json"),
    ]

    results = await router.onboard_locations(new)
    for r in results:
        print(r.location_uid, r.status, r.error or "")
    # If any showed status=failed, re-run with the same `new` list —
    # already-onboarded entries are detected and skipped.

asyncio.run(main())
```

If the 3rd location fails (e.g., a wrong refresh-token-file path), the first two are fully committed and the last two still attempt to onboard. The per-location atomic invariant means no dangling half-records.

## 6. Query the audit log by location and date range

```bash
# All calls to loc_placeholder_001 in May 2026.
python3 scripts/audit_log_query.py \
  --audit-log ./audit-log/podium-router.jsonl \
  --location-uid loc_placeholder_001 \
  --since 2026-05-01 \
  --until 2026-05-31 \
  --output json
```

Output (one record per line):

```json
{"ts": 1715515200.5, "location_uid": "loc_placeholder_001", "org_slug": "kombilife", "endpoint": "/v4/contacts", "method": "POST", "status": 200, "request_id": "abc123def456", "latency_ms": 142.3}
{"ts": 1715515210.7, "location_uid": "loc_placeholder_001", "org_slug": "kombilife", "endpoint": "/v4/conversations", "method": "GET", "status": 200, "request_id": "def789ghi012", "latency_ms": 87.1}
```

Pipe to `jq` for further slicing:

```bash
python3 scripts/audit_log_query.py --location-uid loc_placeholder_001 --since 2026-05-01 --output json \
  | jq -s 'group_by(.status) | map({status: .[0].status, count: length})'
```

## 7. Programmatic compliance answer — which location received this customer's data?

```python
import json
from pathlib import Path

# Compliance asks: "On 2026-05-07 at ~14:07 UTC, a customer named Jane Doe was added to
# our system. Which physical location received that write?"
target_ts = 1715090820   # 2026-05-07 14:07:00 UTC
lines = [json.loads(l) for l in Path("./audit-log/podium-router.jsonl").read_text().splitlines()]
nearby = [l for l in lines if abs(l["ts"] - target_ts) < 60 and l["endpoint"] == "/v4/contacts" and l["method"] == "POST"]
for record in nearby:
    print(f"{record['ts']}: location_uid={record['location_uid']} org={record['org_slug']} req={record['request_id']}")
```

The audit log contains the routing fingerprint; cross-reference the `request_id` with the application's downstream system (CRM, ticketing) to confirm which customer's record was written.

## 8. Per-location bucket sizing override

```yaml
# config/settings.yaml — global defaults
rate_limit:
  default_capacity: 30
  default_refill_per_second: 5
```

```json
// config/locations.json — per-location override
{
  "loc_placeholder_001": {
    "org_slug": "kombilife",
    "client_id": "...",
    "client_secret": "...",
    "refresh_token_file": "./secrets/sydney-refresh.json",
    "rate_limit": {"capacity": 100, "refill_per_second": 20}
  }
}
```

Sydney has higher traffic so its bucket is sized larger. Burleigh Heads inherits the default. A burst at Sydney drains Sydney's bucket only.

## 9. Detect a wrong-org credential pairing

```bash
# Suppose loc_placeholder_001 was accidentally registered with org-B's client_id/secret.
python3 scripts/verify_location.py --location-uid loc_placeholder_001 --credentials-file ./config/locations.json
```

Output:

```
ERR_LOC_002 location_not_in_scope — uid=loc_placeholder_001 not in scope.
Token sees 4 locations; this UID is not one of them.
Scope: loc_placeholder_020, loc_placeholder_021, loc_placeholder_022, loc_placeholder_023
```

Exit code 1. The error message lists the scope so the operator can see immediately that the credential belongs to a different org's locations. The fix: re-onboard `loc_placeholder_001` with the correct OAuth app.

## 10. Integration with podium-webchat-handler (a downstream consumer)

```python
# In a podium-webchat-handler service handling an inbound webhook:
from location_router import LocationRouter
from podium_webchat import handle_inbound_message

router = LocationRouter.from_credentials_file("./config/locations.json",
                                              audit_log_path="./audit-log/podium-router.jsonl")

async def webhook(request):
    payload = await request.json()
    location_uid = payload["location_uid"]   # comes from Podium's webhook body
    client = router.get_client(location_uid)  # raises if unknown; verifies on first call
    # All subsequent API calls flow through the location-scoped client.
    await handle_inbound_message(client, payload)
```

The webhook handler does not need to know about credentials, auth, buckets, or audit logs. It asks the router for a client and the router enforces every guarantee from this skill's six failure modes by construction.
