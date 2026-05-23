# ARD: Podium Webchat Handler

## Architecture Pattern

**Async webhook handler + operator CLIs.** The core is a FastAPI-style webhook handler (`webchat_ingest.py`) that consumes Podium webchat events delivered by the webhook server in `podium-webhook-reliability` (which has already verified HMAC + dedup'd). Around the handler sit four production-engineering layers: an E.164 phone normalizer at the input edge, a race-tolerant contact-upsert path keyed on the normalized phone, a session-state monitor on a periodic scan, and a unified opt-out store consulted on every outbound. Operator CLIs (`phone_normalize.py`, `session_timeout_monitor.py`, `optout_audit.py`) wrap the same library functions for one-off troubleshooting.

Pattern: **Normalize-at-edge + idempotent-upsert + periodic-state-scan + unified-policy-store.**

## Workflow

```
                ┌──────────────────────────────────────────┐
                │  podium-webhook-reliability              │
                │  - HMAC verify                           │
                │  - replay dedup                          │
                └───────────────┬──────────────────────────┘
                                │ verified webchat event
                                ▼
                ┌──────────────────────────────────────────┐
                │  webchat_ingest.process_inbound()        │
                │  ┌────────────────────────────────────┐  │
                │  │ 1. normalize_phone(raw, default)   │  │
                │  │    → E.164 or fail closed          │  │
                │  └─────────────┬──────────────────────┘  │
                │                ▼                          │
                │  ┌────────────────────────────────────┐  │
                │  │ 2. validate_location(loc_uid)      │  │
                │  │    → in VALID_LOCATION_UIDS or 400 │  │
                │  └─────────────┬──────────────────────┘  │
                │                ▼                          │
                │  ┌────────────────────────────────────┐  │
                │  │ 3. check_optout(phone_e164)        │  │
                │  │    → if STOP keyword in body:      │  │
                │  │        record_optout; return       │  │
                │  │    → if previously opted out:      │  │
                │  │        log + return (no reply)     │  │
                │  └─────────────┬──────────────────────┘  │
                │                ▼                          │
                │  ┌────────────────────────────────────┐  │
                │  │ 4. upsert_contact_by_phone(...)    │  │
                │  │    lookup → create → 409 refetch   │  │
                │  └─────────────┬──────────────────────┘  │
                │                ▼                          │
                │  ┌────────────────────────────────────┐  │
                │  │ 5. validate_attachment_size(...)   │  │
                │  │    → ≤ 25 MiB or 413               │  │
                │  └─────────────┬──────────────────────┘  │
                │                ▼                          │
                │  ┌────────────────────────────────────┐  │
                │  │ 6. enqueue downstream message      │  │
                │  │    (agent inbox, CRM mirror, etc.) │  │
                │  └────────────────────────────────────┘  │
                └──────────────────────────────────────────┘

       ┌────────────────────────────────────────────────────┐
       │  background: scan_sessions() every 60s             │
       │  ├ idle > 20m → send_keepalive_prompt              │
       │  └ idle > 28m → persist_partial_state + close      │
       └────────────────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their incident pattern before reading code, then walks through one mitigation per failure in a fixed order.
- **PRD.md** is the product framing — three personas (integration engineer Ravi, frontend engineer Sam, SMB owner Mark archetype), acceptance criteria, success metrics, risk register.
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together.
- **references/errors.md** is a flat `ERR_WEBCHAT_*` lookup table on-call references under stress.
- **references/examples.md** is a cookbook of full worked snippets — every example is runnable end-to-end with the env vars listed at the top.
- **references/implementation.md** is the portability + wiring layer: Node.js equivalents, FastAPI integration, opt-out store schema choices (SQL vs Redis vs DynamoDB).
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON on stdout, human on stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read           # read config, contact mirror snapshots, audit logs
  - Write          # write audit reports, opt-out store schema migrations
  - Edit           # edit widget config files to add location_uid hints
  - Bash(curl:*)   # call Podium contacts / locations / messages endpoints in shell examples
  - Bash(jq:*)     # parse Podium responses in shell examples
  - Bash(python3:*) # invoke the operator scripts
  - Grep           # audit the integration source for hardcoded phones / location_uids
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files and never makes git commits. Audits draft reports for the operator; the operator commits.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-webchat-handler/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # session timeouts, attachment limits, opt-out keywords, default country
├── references/
│   ├── errors.md              # ERR_WEBCHAT_001..014 with cause + solution
│   ├── examples.md            # 10 worked examples
│   └── implementation.md      # Node equivalents, FastAPI wiring, opt-out store schema
└── scripts/
    ├── phone_normalize.py          # CLI: parse + E.164 + carrier metadata
    ├── webchat_ingest.py           # FastAPI handler (also runnable as a library)
    ├── session_timeout_monitor.py  # CLI: scan in-flight sessions
    └── optout_audit.py             # CLI: confirm opt-out flag across all layers
```

## API Integration Architecture

The Podium webchat surface used by this skill is six endpoints. Each is wrapped by exactly one function:

| Endpoint | Function | Notes |
|---|---|---|
| `GET /v4/contacts?phone=...&location_uid=...` | `lookup_contact_by_phone()` | First step of the upsert path |
| `POST /v4/contacts` | `create_contact()` | Second step; tolerates 409 |
| `PATCH /v4/contacts/{uid}` | `mark_contact_optout_in_podium()` | Mirror opt-out to Podium's compliance view |
| `GET /v4/locations` | `load_locations()` | Run at startup + periodic refresh; populates `VALID_LOCATION_UIDS` |
| `POST /v4/conversations/{uid}/messages` | `send_webchat_reply()` | Goes through `podium-rate-limit-survival` |
| `POST /v4/conversations/{uid}/close` | `close_session_cleanly()` | Called by `scan_sessions` at the 28 min threshold |

All six calls flow through a `PodiumAuth` instance from `podium-auth` for token caching, scope validation, and decay monitoring.

## Data Flow Architecture

```
[Podium]            [Webhook svc]        [Webchat handler]      [Stores]            [Agent / CRM]
   │                     │                       │                  │                      │
   │ POST event          │                       │                  │                      │
   ├────────────────────►│                       │                  │                      │
   │                     │ HMAC + dedup OK       │                  │                      │
   │                     ├──────────────────────►│                  │                      │
   │                     │                       │ normalize phone  │                      │
   │                     │                       │ validate loc_uid │                      │
   │                     │                       │ check opt-out    │                      │
   │                     │                       ├─────────────────►│                      │
   │                     │                       │     opt-out store│                      │
   │                     │                       │◄─────────────────┤                      │
   │ GET /contacts       │                       │                  │                      │
   │◄────────────────────┼───────────────────────┤                  │                      │
   │ POST /contacts (409)│                       │                  │                      │
   │◄────────────────────┼───────────────────────┤                  │                      │
   │ GET refetch         │                       │                  │                      │
   │◄────────────────────┼───────────────────────┤                  │                      │
   │                     │                       │ upsert local     │                      │
   │                     │                       ├─────────────────►│                      │
   │                     │                       │  contact mirror  │                      │
   │                     │                       │                  │ enqueue              │
   │                     │                       ├──────────────────┼─────────────────────►│
```

The opt-out store and the contact mirror are independent stores. They share only the `phone_e164` natural key. This isolation lets the opt-out path keep running even if the contact mirror is degraded.

## Error Handling Strategy

Four error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PhoneValidationError` | `phonenumbers.parse` failure or invalid number | Refuse the webchat submission; surface inline to the customer |
| `WebchatError` (transient) | 5xx from Podium, network timeout | Retry with exponential backoff via `podium-rate-limit-survival` |
| `WebchatError` (permanent) | 400 invalid_phone, invalid_location_uid; 451 opted_out | Surface to handler; no retry value |
| `AttachmentTooLargeError` | Attachment > 25 MiB | Reject client-side; never POST to Podium |

The 409 contact_already_exists case is intentionally NOT an error — it is the expected race-loser path and resolves with a refetch.

## Composability & Stacking

`podium-webchat-handler` is a **mid-stack consumer** in the podium-pack:

```
                        podium-webchat-handler ◄── this skill
                         /        │        \
                        ▼         ▼         ▼
        podium-webhook-      podium-      podium-rate-
        reliability          auth         limit-survival
                              │
                              ▼
                   (foundation auth layer)

        peer reference: podium-contact-dedup
        (deeper dedup mechanics for cross-source conflicts)
```

A consumer of this skill holding a working `PodiumAuth` instance and a configured `podium-webhook-reliability` webhook server gets webchat ingest with phone normalization, race-tolerant upsert, session-timeout monitoring, attachment validation, location routing, and opt-out propagation without re-implementing any of it. `podium-contact-dedup` is referenced rather than depended on — it solves the harder cross-source conflict case that goes beyond same-phone duplicates.

## Performance & Scalability

- **Per-message latency**: dominated by the contact lookup (~50–150ms Podium-side). Local cache of the phone → contact_uid mapping with a 5 min TTL drops this to ~5ms for warm contacts. Cache invalidates on the opt-out write path.
- **Session scan cost**: O(active_sessions) per 60s tick. With 10k active sessions, ~10ms wall time — trivial.
- **Contact-mirror writes**: one row per unique phone; the unique-index constraint is the throughput bottleneck under simultaneous-arrival load. Postgres unique-index handles 10k+/s comfortably.
- **Opt-out check on outbound**: one read per outbound attempt. Backed by Redis or a Postgres prepared-statement table; submillisecond.
- **Locations refresh**: every 5 minutes from `/v4/locations`. Negligible cost; protects against new locations being added mid-day.

## Security & Compliance

- **PII handling**: phone numbers are PII in most jurisdictions. The opt-out store and contact mirror must encrypt at rest. Logs must redact phones except for the last 4 digits in operator-facing output.
- **Opt-out compliance**: STOP keywords trigger an opt-out write before any reply is composed. The opt-out is mirrored to Podium so their compliance view matches yours. The cache TTL is bounded at 60s.
- **Cross-tenant isolation**: in a multi-tenant deployment (agency case), the contact mirror and opt-out store are partitioned by org slug. A query for `(phone, location_uid)` in org A cannot return a row from org B.
- **Audit trail**: every inbound event logs `{event_id, phone_last4, location_uid, action, latency_ms}` as structured JSON. No full phones, no message bodies. Bodies are stored in the conversation history with separate access control.
- **Attachment validation**: client-side size check + server-side `Content-Length` check + MIME-type allowlist. Reject early.

## Testing Strategy

- **Unit tests**:
  - `phone_normalize` for AU, US, UK, fully international (`+`-prefixed) inputs and explicit fail-closed cases
  - `upsert_contact_by_phone` for the 409-refetch branch (race-loser path)
  - `validate_location` for empty, valid, and unknown `location_uid`
  - `check_optout` cache TTL bound (returns stale within 60s, fresh after)
  - `validate_attachment_size` for ≤25 MiB pass and >25 MiB raise
- **Integration tests**: against a Podium sandbox org with at least two `location_uid`s; verify a full ingest cycle for each location and assert no cross-location routing.
- **Race test**: 100 concurrent ingest tasks for the same phone produce exactly 1 contact record.
- **Session-timeout test**: stub `time.time()` forward 20 min (warn fires) and 28 min (close fires + partial_state persisted + hydratable on next message).
- **Opt-out propagation test**: STOP via SMS handler → 30s sleep → outbound via webchat handler is blocked; symmetric in the other direction.
- **Soak test**: 24h run with synthetic webchat events; verify zero duplicate contacts, zero unblocked outbound to opted-out phones, zero wrong-location routings.
