# Implementation Reference — podium-webchat-handler

Language-portability layer plus FastAPI wiring plus opt-out store schema choices plus the locations-refresh background pattern.

## Node.js / TypeScript port

The Python normalizer + upsert + session model translates to TypeScript with these substitutions: `phonenumbers` → `libphonenumber-js`, `phonenumbers.carrier` is not available in the JS port (use a separate carrier lookup if you need it), and `dataclasses` → plain interfaces.

```typescript
import { parsePhoneNumberFromString, isValidNumber } from "libphonenumber-js";

export class PhoneValidationError extends Error {}

export function normalizePhone(raw: string, defaultCountry: string = "AU"): string {
  const parsed = parsePhoneNumberFromString(raw, defaultCountry as any);
  if (!parsed || !parsed.isValid()) {
    throw new PhoneValidationError(`invalid phone for ${defaultCountry}: ${raw}`);
  }
  return parsed.number;   // already E.164
}
```

```typescript
interface PodiumAuth { getToken(): Promise<string>; }

export async function upsertContactByPhone(
  auth: PodiumAuth,
  phoneE164: string,
  locationUid: string,
  firstName?: string,
  lastName?: string,
): Promise<any> {
  const token = await auth.getToken();
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  // Lookup
  const lookup = await fetch(
    `https://api.podium.com/v4/contacts?phone=${encodeURIComponent(phoneE164)}` +
      `&location_uid=${encodeURIComponent(locationUid)}`,
    { headers },
  );
  if (lookup.ok) {
    const body = await lookup.json();
    if (body.data?.length) return body.data[0];
  }

  // Create
  const create = await fetch("https://api.podium.com/v4/contacts", {
    method: "POST", headers,
    body: JSON.stringify({ phone: phoneE164, location_uid: locationUid,
                           first_name: firstName, last_name: lastName }),
  });
  if (create.ok) return create.json();

  if (create.status === 409) {
    const refetch = await fetch(
      `https://api.podium.com/v4/contacts?phone=${encodeURIComponent(phoneE164)}` +
        `&location_uid=${encodeURIComponent(locationUid)}`,
      { headers },
    );
    if (refetch.ok) {
      const body = await refetch.json();
      if (body.data?.length) return body.data[0];
    }
  }
  throw new Error(`upsert failed ${create.status}: ${await create.text()}`);
}
```

## FastAPI deployment wiring

The webhook handler is small enough to live in a single file. The two background tasks (session scanner and locations refresher) need lifespan hooks:

```python
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from podium_auth import PodiumAuth

auth: PodiumAuth = ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_locations(auth)
    session_task   = asyncio.create_task(session_loop(active_sessions))
    locations_task = asyncio.create_task(periodic_location_refresh(auth, interval_s=300))
    yield
    session_task.cancel()
    locations_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/podium/webchat")
async def webchat_webhook(req: Request):
    payload = await req.json()
    await process_inbound_webchat(payload, auth)
    return {"status": "ok"}
```

Deploy behind a reverse proxy (nginx / Caddy) that already terminates TLS. `podium-webhook-reliability` provides the HMAC-verifying middleware that gates this endpoint.

## Opt-out store schema choices

### Postgres (recommended for most deployments)

```sql
CREATE TABLE optout_records (
    phone_e164          text PRIMARY KEY,                 -- natural key
    source_channel      text NOT NULL,                    -- 'sms' | 'webchat' | 'manual' | 'api'
    recorded_at         timestamptz NOT NULL DEFAULT now(),
    recorded_by         text,                             -- agent uid or 'inbound-keyword'
    notes               text
);

CREATE INDEX optout_records_recorded_at_idx ON optout_records (recorded_at DESC);
```

The PK on `phone_e164` is what makes the dedup race-free at the DB layer. A racing INSERT with the same phone hits the PK constraint and you fall through to a "look up the winner" path identical to the Podium 409 refetch.

### Redis (highest-throughput option; pair with a Postgres source-of-truth)

```
SET optout:+61412345678 '{"source":"sms","recorded_at":1746000000}'
EXPIRE optout:+61412345678 0   # do NOT expire — opt-out is permanent
```

The Redis copy is a read-cache. Writes go to Postgres first; Redis is invalidated and refreshed on the next read. Bound the cache TTL at 60s per `optout.cache_ttl_seconds`.

### DynamoDB (AWS-native deployments)

```
Table: optout-records
  Partition key: phone_e164 (string)
  Attributes: source_channel, recorded_at, recorded_by, notes
  Stream: enabled (so a downstream Lambda mirrors to Podium /v4/contacts PATCH)
```

DynamoDB's conditional `PutItem` (`ConditionExpression: attribute_not_exists(phone_e164)`) handles the race; on conditional-write failure, the racing record is the source of truth.

## Locations periodic refresh pattern

```python
import asyncio, time

locations_last_refreshed_at: float = 0.0

async def periodic_location_refresh(auth: PodiumAuth, interval_s: int = 300) -> None:
    global locations_last_refreshed_at
    while True:
        try:
            await load_locations(auth)
            locations_last_refreshed_at = time.time()
        except Exception as e:
            log_warn(f"locations refresh failed: {e}")
        await asyncio.sleep(interval_s)

def check_locations_freshness(interval_s: int = 300) -> None:
    if locations_last_refreshed_at == 0:
        raise RuntimeError("ERR_WEBCHAT_014 locations never loaded — startup hook failed")
    age = time.time() - locations_last_refreshed_at
    if age > 2 * interval_s:
        raise RuntimeError(f"ERR_WEBCHAT_014 locations refresh stale: {age:.0f}s")
```

## Contact mirror schema (local CRM)

If you maintain a local mirror of Podium contacts, the schema is:

```sql
CREATE TABLE contacts (
    contact_uid     text PRIMARY KEY,        -- Podium-assigned uid
    phone_e164      text NOT NULL,           -- normalized; NEVER store local format
    location_uid    text NOT NULL,
    first_name      text,
    last_name       text,
    opted_out       boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX contacts_phone_location_uniq
    ON contacts (phone_e164, location_uid);   -- THE dedup gate

CREATE INDEX contacts_opted_out_partial
    ON contacts (phone_e164) WHERE opted_out = true;
```

The unique index on `(phone_e164, location_uid)` is the structural enforcement of the dedup contract. The handler code is the first line of defense; the index is the floor.

## Partial-state buffer storage

Three options, ranked:

1. **Filesystem (default)** — one JSON file per `(phone_e164, location_uid)` pair. Simple, atomic-rename-safe, no extra dependency. Works for single-node deployments.
2. **Redis** — one key per pair with no TTL (or a long TTL like 24h). Necessary for horizontally-scaled deployments where any node may handle the next message.
3. **Postgres row in `webchat_sessions` table** — most durable, but adds a write+read on every session close + resume.

```sql
CREATE TABLE webchat_partial_state (
    phone_e164    text NOT NULL,
    location_uid  text NOT NULL,
    partial_state jsonb NOT NULL,
    persisted_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (phone_e164, location_uid)
);
```

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_normalize_phone_au_us_uk` | unit | E.164 produced correctly for the documented locales |
| `test_normalize_phone_fails_closed_on_unparseable` | unit | `PhoneValidationError` raised on garbage input |
| `test_upsert_409_refetch_returns_winner` | unit | 409 path resolves to the racing creator's record |
| `test_upsert_concurrent_one_record` | concurrency | 100 simultaneous upserts → exactly 1 row |
| `test_session_close_persists_partial_state` | unit | After 28 min idle, `partial_state` written |
| `test_session_resume_hydrates_state` | unit | Next message from same `(phone, loc)` rehydrates |
| `test_attachment_size_413` | unit | > 25 MiB raises `AttachmentTooLargeError` |
| `test_validate_location_no_default` | unit | Empty `location_uid` raises; never falls back |
| `test_optout_propagates_sms_to_webchat` | integration | STOP via SMS → webchat outbound blocked within 60s |
| `test_optout_propagates_webchat_to_sms` | integration | STOP via webchat → SMS outbound blocked within 60s |
| `test_optout_store_unreachable_fails_closed` | integration | Store outage blocks outbound, does not permit |

## Library packaging notes

This skill ships the library inline in `SKILL.md` and `references/examples.md` rather than as a separate pip package, for the same reasons as `podium-auth`: ~200 lines total, every integration needs a custom opt-out and contact mirror binding, and an extracted package would add versioning overhead without enabling material reuse. If three concrete callers depend on identical behavior, promote to `@intentsolutions/podium-webchat-handler` on npm or `intent-podium-webchat-handler` on PyPI.

## Cross-skill composition

- **Upstream (consumed by this skill)**:
  - `podium-auth` provides `PodiumAuth` for OAuth token caching, scope validation, decay monitoring.
  - `podium-webhook-reliability` provides the HMAC-verifying webhook server + replay dedup. This handler is wired as a downstream consumer of that server's verified-event channel.
  - `podium-rate-limit-survival` wraps every outbound `POST /v4/conversations/{uid}/messages` call with the rate-limit-aware backoff policy.

- **Adjacent (referenced, not consumed)**:
  - `podium-contact-dedup` handles cross-source conflict resolution (same phone, conflicting names across SMS / webchat / reviews / call transcripts). This skill prevents the most common same-channel race; that skill handles the harder reconciliation.
