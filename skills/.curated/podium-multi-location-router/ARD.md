# ARD: Podium Multi-Location Router

## Architecture Pattern

**Library + scripts on top of two upstream skills.** The core of this skill is a routing library (`LocationRouter`, `PodiumLocationClient`) that sits between the application and the lower-level `podium-auth` and `podium-rate-limit-survival` skills. The router holds a map of `location_uid → (PodiumAuth, TokenBucket, LocationCredential)`, pre-flight-verifies every call against `GET /v4/locations`, emits a JSONL audit line per call, and orchestrates idempotent onboarding of new locations. The operator-facing CLI scripts wrap the library for one-off verification, onboarding, and audit-log queries.

Pattern: **Per-key dispatch with single-flight verification, append-only audit, and atomic per-key onboarding.**

## Workflow

```
                  ┌──────────────────────────────────┐
                  │ Application code                 │
                  │ client = router.get_client(uid)  │
                  │ await client.call("POST", "/v4/contacts", ...) │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 1. Resolve location_uid          │
                  │    → cred = _creds[location_uid] │
                  │    → unknown? raise              │
                  │      UnknownLocationError        │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 2. Pre-flight verify ownership   │
                  │    if verified_at age > 1h:      │
                  │      GET /v4/locations           │
                  │      assert uid in returned set  │
                  │      not in set? raise           │
                  │        LocationNotInScopeError   │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 3. Acquire per-location bucket   │
                  │    await bucket.acquire()        │
                  │    bucket is sized independently │
                  │    of org-wide quota             │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 4. Fetch scoped access token     │
                  │    token = await auth.get_token()│
                  │    (auth is a per-uid PodiumAuth)│
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 5. Execute HTTP call             │
                  │    httpx.AsyncClient.request(... │
                  │      headers={                   │
                  │        Authorization: Bearer ..  │
                  │        X-Request-ID: <uuid>      │
                  │      })                          │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 6. Emit audit log line           │
                  │    append-only JSONL:            │
                  │    {ts, location_uid, org_slug,  │
                  │     endpoint, method, status,    │
                  │     request_id, latency_ms}      │
                  └──────────────────┬───────────────┘
                                     │
                                     ▼
                          return httpx.Response

         ┌──────────────────────────────────────────┐
         │ onboarding (separate flow):              │
         │ for cred in new_locations:               │
         │   if uid in map: skip_existing           │
         │   persist_credential(cred)               │
         │   build PodiumAuth + TokenBucket         │
         │   verify uid against /v4/locations       │
         │   on any failure: rollback per-uid       │
         └──────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** opens with the six production failure modes so a reader recognizes their problem immediately, then walks through one mitigation per failure in a fixed order. Code snippets are inline; long-form code lives in `scripts/`.
- **PRD.md** frames the work for stakeholders (acceptance criteria per user story, success metrics, risk register) — useful when justifying the routing layer to a non-engineer agency owner.
- **ARD.md** (this document) is the engineer's reference for how the routing library fits between the application and the two upstream skills.
- **references/errors.md** is a flat `ERR_LOC_*` lookup table on-call references under stress when an audit-log query surfaces an unexpected status.
- **references/examples.md** is a cookbook of full worked snippets — agency-scale, single-store, audit query, partial-failure onboarding recovery.
- **references/implementation.md** is the portability layer: Node.js port of the router, SQLite-backed audit-log query for >1M-line logs, integration with the upstream skills' Node ports.
- **scripts/** are executable operator tools, each single-responsibility with JSON-on-stdout and human-on-stderr for shell-pipeline composition.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read              # read credentials file, settings, audit-log queries
  - Write             # write new credential entries, audit-log files
  - Edit              # edit credentials map atomically during onboarding
  - Bash(curl:*)      # call Podium /v4/locations in shell examples
  - Bash(jq:*)        # parse Podium responses and slice audit-log JSONL
  - Bash(python3:*)   # invoke the operator scripts
  - Bash(sqlite3:*)   # query an audit log that has been imported to SQLite
  - Grep              # scan the audit log for forensic queries
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files (audit log is append-only by policy) and never makes git commits. Onboarding writes a credential entry; the operator commits.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-multi-location-router/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # verify TTL, audit-log path, per-location bucket defaults
├── references/
│   ├── errors.md              # ERR_LOC_001..012 with cause + solution
│   ├── examples.md            # 10 worked examples (agency, multi-store, onboarding, audit)
│   └── implementation.md      # Node port, SQLite audit query, audit-log retention
└── scripts/
    ├── location_router.py     # library: LocationRouter + PodiumLocationClient
    ├── verify_location.py     # CLI: confirm a location_uid is in scope
    ├── onboard_location.py    # CLI: idempotently onboard a new location
    └── audit_log_query.py     # CLI: query the audit log by uid + date range
```

## API Integration Architecture

The Podium surface this skill touches is four endpoints, each wrapped at exactly one call site:

| Endpoint | Method | Wrapping |
|---|---|---|
| `GET /v4/locations` | `LocationRouter.ensure_location_verified()` | Pre-flight; single-flight per `location_uid` per TTL window |
| `POST /v4/contacts`, `/v4/conversations`, etc. | `PodiumLocationClient.call()` | Generic dispatch; all data-plane writes flow through here |
| `GET /v4/contacts/{id}`, etc. | `PodiumLocationClient.call()` | Same generic dispatch — reads use the same path so reads also produce audit lines |

A single `httpx.AsyncClient` factory inside `PodiumLocationClient` keeps connections pooled per location. Memory cost is O(num_locations) — trivial for the 50–500 location agency case.

## Data Flow Architecture

```
[Credentials Map]   [Per-uid PodiumAuth]   [Podium API]      [Audit Log]    [App code]
       │                    │                   │                 │              │
       │  load on startup   │                   │                 │              │
       ├───────────────────►│                   │                 │              │
       │                    │                   │                 │              │
       │                    │                   │       client.call("POST", ...) │
       │                    │                   │                 │              │
       │     resolve uid    │                   │                 │              │
       │ ◄──────────────────┤                   │                 │              │
       │                    │                   │                 │              │
       │                    │   GET /v4/locations (first call or TTL expired)    │
       │                    ├──────────────────►│                 │              │
       │                    │ ◄ {locations: [{uid: ...}]}         │              │
       │                    │                   │                 │              │
       │                    │   get_token()                       │              │
       │                    │   POST <path>     │                 │              │
       │                    ├──────────────────►│                 │              │
       │                    │ ◄ 200 / 4xx / 5xx │                 │              │
       │                    │                   │                 │              │
       │                    │                   │   append JSONL line            │
       │                    │                   ├────────────────►│              │
       │                    │                   │                 │              │
       │                    │                   │                 │  Response    │
       │                    │                   │                 ├─────────────►│
```

The audit-log write is the critical side-effect — it must happen for every call regardless of outcome (200, 4xx, 5xx, or timeout). The library catches and re-raises HTTP exceptions after the audit emit so the trail is complete even when the call fails.

## Error Handling Strategy

Three error classes specific to this skill, plus the upstream `PodiumAuthError` from `podium-auth`:

| Class | Trigger | Caller behavior |
|---|---|---|
| `UnknownLocationError` (extends `KeyError`) | `get_client(uid)` for a uid not in the map | Caller fixes the call or runs `onboard_location.py`; no automated recovery |
| `LocationNotInScopeError` (extends `PodiumAuthError`) | Pre-flight `GET /v4/locations` does not contain the requested uid | Operator runs `verify_location.py`; likely the credential is for the wrong org |
| `LocationRateLimitExceeded` | `TokenBucket.acquire()` cannot acquire within timeout | Caller honors retry backoff; tune bucket capacity in `config/settings.yaml` |
| `OnboardingPartialFailure` | One or more locations in a bulk onboard failed | Caller re-runs `onboard_location.py`; already-onboarded are skipped |

`UnknownLocationError` is a hard failure with no retry — there is no scenario where retrying a typo'd uid makes sense.

## Composability & Stacking

This skill is the **multi-location dispatch layer**. It depends on the two skills below it and is consumed by every data-plane skill above it.

```
podium-webchat-handler        podium-review-request-automation        podium-call-transcript-pipeline
              │                              │                                        │
              └──────────────┬───────────────┴────────────────────────────────────────┘
                             │
                             ▼
                  podium-multi-location-router    ◄── this skill
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
   podium-rate-limit-survival    podium-auth
   (per-location bucket)         (PodiumOrgRouter pattern)
```

A consumer skill that holds a `LocationRouter` instance gets pre-flight verification, per-location rate limiting, per-location auth isolation, and audit logging for free. The consumer skill's only responsibility is to pass the correct `location_uid` for the customer the call is for.

## Performance & Scalability

- **Per-call overhead**: one map lookup (O(1)) + one bucket acquire (microseconds when bucket has capacity) + one audit-log append (sub-millisecond on local disk). Negligible compared to the network call.
- **Verification overhead**: one `GET /v4/locations` per location per hour. For an agency with 500 locations, that is 500 calls/hour = ~1 call every 7 seconds — well within Podium's per-org rate limit if spread across 50+ orgs.
- **Bulk onboarding**: serial (one location at a time); 5–10 locations onboard in 30–60 seconds including verification. Concurrency is intentionally avoided to keep the atomic-per-location invariant simple.
- **Audit log throughput**: append-only JSONL handles thousands of writes per second on local disk. For agencies at 100k+ calls/day, see `references/implementation.md` § "SQLite audit-log layer" for the query-side index.
- **Memory cost**: O(num_locations) for the map + auth instances + buckets. ~5 KB per location; 500 locations ≈ 2.5 MB.

## Security & Compliance

- **Credentials at rest**: SOPS + age (Intent Solutions standard) for production. Plaintext credential maps in dev only.
- **Audit log contents**: no tokens, no request bodies, no PII — routing fingerprint only (`location_uid`, `org_slug`, `endpoint`, `method`, `status`, `request_id`, `latency_ms`, `ts`).
- **Audit log retention**: 6 months minimum (compliance default). Rotation is operator-controlled via logrotate; the library never deletes audit lines.
- **Pre-flight verification**: `GET /v4/locations` is the boundary that proves the credential actually owns the `location_uid` before any write. A `LocationNotInScopeError` is loud enough to surface in the next deploy review.
- **Per-location credential isolation**: a leaked credential affects exactly one location's traffic, not the whole org's. Rotation (via `podium-auth.rotate_secret.py`) is per-location.

## Testing Strategy

- **Unit tests**: mock `httpx` for the four router happy paths (verified call, first-call verification, cache-hit, cache-miss-then-verify) plus the three failure modes (`UnknownLocationError`, `LocationNotInScopeError`, partial-failure onboarding).
- **Integration tests**: against a Podium sandbox with two real fixture locations under one OAuth app; verify pre-flight, audit-log emission, per-location bucket isolation.
- **Onboarding idempotence test**: onboard 5 locations, simulate failure on the 3rd, re-run with the same input, assert exactly the originally-failed location is processed on the retry.
- **Audit-log schema test**: parse 100k synthetic audit lines and assert every line has all 8 required fields; no `null` values; no token-like substrings.
- **Cross-contamination test**: under concurrent load (10 locations, 1000 requests each), assert every audit line's `location_uid` matches the requested location and that no auth instance was reused across locations.
- **Rate-limit isolation test**: drain one location's bucket; assert all other locations' buckets remain at capacity and serve traffic normally.
