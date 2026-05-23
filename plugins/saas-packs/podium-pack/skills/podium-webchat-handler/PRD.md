# PRD: Podium Webchat Handler

## Summary

**One-liner**: Production-grade ingest handler for Podium webchat — strict E.164 phone validation at the widget edge, race-tolerant contact upsert keyed on phone, session-timeout monitoring with partial-state buffering, attachment-size pre-validation, multi-location routing with no default fallback, and unified opt-out propagation across SMS + webchat.

**Domain**: SaaS integration / SMB customer-engagement platforms / messaging compliance

**Users**: Integration engineers, frontend engineers building chat widgets, small-business owners operating multi-location storefronts on Podium

## Problem Statement

Podium webchat is the lowest-friction inbound channel a SMB exposes — a "Chat with us" widget on a public website. Six failure modes ship with the off-the-shelf integrations and each one is invisible until it has already produced an incident. A phone collected in local format silently fails the later SMS reply. Two simultaneous webchats from the same phone produce two contact records and split the conversation history. A session expires mid-multiple-choice answer and the agent picks up the conversation in fresh context. A 26 MiB photo upload fails after the customer waits through the progress bar. A multi-location org routes Brisbane customers to the Sydney queue because the widget didn't pass `location_uid`. A STOP keyword recorded in SMS doesn't propagate to webchat fast enough and the next session trips a compliance violation.

The off-the-shelf Podium SDKs and the embedded widget defaults do not address any of these failure modes by construction. This skill installs the production-engineering layer that prevents each one.

## Target Users

### Persona 1: Integration Engineer (Ravi)

- **Role**: Builds and operates the webhook handler that ingests Podium webchat events into a multi-location SMB's CRM mirror.
- **Goals**: Zero duplicate contacts; zero silent SMS-reply failures; zero compliance violations from stale opt-out state; an audit log that survives a privacy-regulator request.
- **Pain Points**: Discovered three months of "duplicate contact" support tickets traced to a TOCTOU race on the contact-creation path. Got paged on a Saturday because a customer's STOP propagated to SMS but not webchat, then a webchat reply trip-wired the compliance dashboard.
- **Technical Level**: High (async Python / Node fluent; has built webhook handlers before; reads HTTP traces under stress).

### Persona 2: Frontend Engineer (Sam)

- **Role**: Owns the embeddable chat widget on the SMB's public website(s). Multi-location org with two storefronts (Sydney and Burleigh Heads).
- **Goals**: A widget that "just works" across both stores; immediate phone-validation feedback (red field on a malformed number, not a server-side rejection 800ms later); attachment-size feedback before the upload starts.
- **Pain Points**: Has been bitten by widget code that calls the API with the customer's locally-formatted phone and a hardcoded `location_uid`. The Sydney widget routed Brisbane traffic for two weeks before anyone noticed.
- **Technical Level**: Medium-High (TypeScript/React fluent, less comfortable with the server-side dedup mechanics).

### Persona 3: Small-Business Owner (Mark archetype)

- **Role**: Owner-operator of a multi-location campervan/RV rental business (the Kombi/RV pattern). Does not write code. Pays a contractor to build and maintain the integration.
- **Goals**: When a customer reaches out via the website chat widget, the right store gets the message. Returning customers are recognized, not re-created. Customers who opt out stay opted out. Compliance audits show clean records.
- **Pain Points**: Lost a customer who got routed to the wrong store and was told "sorry, that's the other location, can you call them?" Got a written complaint from a customer who STOP'd via SMS and still received a webchat-triggered SMS the next week. Discovered duplicate contact records when the rebooking flow showed two histories.
- **Technical Level**: Low — relies on the integration to be invisible and correct.

## User Stories

### US-1: E.164 phone normalization at the widget (P0)

**As** a frontend engineer,
**I want** every phone collected by the widget to be normalized to E.164 with a country default appropriate to the location,
**So that** no later SMS reply attempt can fail because of a locally-formatted number.

**Acceptance Criteria:**

- `normalize_phone(raw, default_country)` returns E.164 form or raises `PhoneValidationError`
- The widget passes `default_country` from the location context, never hardcodes
- A raw phone that cannot be parsed for the supplied country fails closed — the widget refuses to accept the submission and surfaces the error inline
- Australian and US local formats are tested explicitly (`0412 345 678` → `+61412345678`, `(415) 555-1234` → `+14155551234`)

### US-2: Race-tolerant contact upsert (P0)

**As** an integration engineer,
**I want** the contact-creation path to be idempotent under simultaneous arrivals from the same phone,
**So that** no human ever ends up as two contact records.

**Acceptance Criteria:**

- The handler does lookup-by-phone, then create-on-miss, then refetch-on-409
- Local contact mirror enforces a unique index on the E.164 phone column
- Two simultaneous handler runs with the same phone produce exactly one contact record (verified by concurrent test)
- A 409 from Podium is treated as a successful upsert (the racing creator won; we return their record)

### US-3: Session-timeout monitoring with partial-state buffering (P0)

**As** an integration engineer,
**I want** in-flight sessions monitored on a ~60s scan,
**So that** customers who walk away mid-answer can resume without restating the conversation.

**Acceptance Criteria:**

- A session idle > 20 min triggers a keepalive prompt to the customer
- A session idle > 28 min is closed cleanly with its `partial_state` persisted
- On the next message from the same `phone_e164 + location_uid` pair, the persisted `partial_state` is hydrated and made available to the agent
- The 28 min close threshold is strictly below Podium's documented server-side expiry — we never let Podium silently expire a session

### US-4: Client-side attachment validation (P1)

**As** a frontend engineer,
**I want** an explicit size check before any upload begins,
**So that** the customer is told immediately that their attachment is too large, not after a 30-second progress bar.

**Acceptance Criteria:**

- `validate_attachment_size(size_bytes)` raises `AttachmentTooLargeError` at `> 25 MiB`
- The widget wires this to the file-input `change` event
- The server-side handler also validates `Content-Length` and returns 413 before forwarding to Podium

### US-5: Multi-location routing with no default fallback (P1)

**As** a small-business owner running multiple storefronts,
**I want** every webchat message routed to the correct location's queue,
**So that** customers are not handed off to a store they were not asking about.

**Acceptance Criteria:**

- `validate_location(location_uid)` raises if `location_uid` is missing or unknown
- The valid-location set is loaded from Podium `/v4/locations` at startup (and refreshed periodically)
- The handler has NO default-location fallback — missing `location_uid` is a hard error surfaced to the widget operator
- Each store has its own widget embed snippet carrying its own `location_uid`

### US-6: Unified opt-out propagation (P1)

**As** an SMB owner subject to messaging-compliance rules,
**I want** a STOP keyword in either channel (SMS or webchat) to suppress outbound traffic in both,
**So that** I do not trip a compliance violation when a customer has clearly opted out.

**Acceptance Criteria:**

- A single opt-out store keyed on `phone_e164`, consulted by both the SMS handler and the webchat handler
- STOP keywords (`STOP`, `UNSUBSCRIBE`, `QUIT`, `END`, `CANCEL`, `OPTOUT`) trigger an opt-out write on inbound
- Outbound attempts on either channel check the opt-out store before sending
- The opt-out cache TTL is at most 60 seconds — long enough for performance, short enough to avoid propagation lag

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | All phones must be normalized to E.164 using `phonenumbers` before storage or outbound |
| REQ-2 | Contact creation must be a race-tolerant idempotent upsert keyed on `phone_e164` |
| REQ-3 | Local contact mirror must have a database-level unique index on `phone_e164` |
| REQ-4 | Session-timeout monitor must run on a ≤ 60s cadence with two thresholds (warn, close) |
| REQ-5 | Closed sessions must persist `partial_state` for hydration on the next message |
| REQ-6 | Attachment size must be validated client-side and server-side against the 25 MiB limit |
| REQ-7 | `location_uid` must be validated against a startup-loaded set; no default fallback |
| REQ-8 | Opt-out must be a single store consulted by both SMS and webchat outbound paths |
| REQ-9 | Opt-out cache TTL must be ≤ 60 seconds |
| REQ-10 | The handler must consume `podium-webhook-reliability` for HMAC verification + dedup |
| REQ-11 | The handler must consume `podium-auth` for OAuth token caching |
| REQ-12 | The handler must consume `podium-rate-limit-survival` for outbound rate-limit handling |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/contacts` | GET | Lookup contact by phone + location_uid |
| `https://api.podium.com/v4/contacts` | POST | Create contact (idempotent upsert path) |
| `https://api.podium.com/v4/contacts/{uid}` | PATCH | Update contact opt-out flag |
| `https://api.podium.com/v4/locations` | GET | Load valid `location_uid` set at startup |
| `https://api.podium.com/v4/conversations/{uid}/messages` | POST | Send a webchat reply or attachment |
| `https://api.podium.com/v4/conversations/{uid}/close` | POST | Cleanly close an expiring session |

## Non-Goals

- This skill does not implement the embeddable widget itself — it ships the validation logic the widget must run; the actual UI is the SMB's responsibility.
- This skill does not implement the harder cross-source contact-dedup cases (same phone, conflicting names across SMS + webchat + reviews); those live in `podium-contact-dedup`.
- This skill does not implement OAuth — `podium-auth` is a prerequisite.
- This skill does not implement webhook signature verification or dedup — `podium-webhook-reliability` is a prerequisite.
- This skill does not implement outbound rate-limit handling — `podium-rate-limit-survival` is a prerequisite.

## Success Metrics

| Metric | Target |
|---|---|
| Duplicate contact records created per quarter | 0 |
| Silent SMS-reply failures due to non-E.164 phone | 0 |
| Mid-conversation context loss incidents (customer asked to restart) | 0 per month |
| Wrong-location routing incidents | 0 per month |
| Opt-out compliance violations | 0 per quarter |
| Attachment 413s reaching the user | < 1% of attachment attempts |

## Constraints & Assumptions

- Podium's webchat session expiry is approximately 30 minutes idle (used as the ceiling for the 28 min close threshold). If Podium changes this, the close threshold must drop proportionally.
- Podium's attachment limit is 25 MiB (documented). If it changes, `PODIUM_ATTACHMENT_MAX_BYTES` updates accordingly.
- The integration has access to a contact store (local DB or KV) with a unique-index facility on the phone column.
- The integration has access to an opt-out store consulted by both SMS and webchat code paths (a shared row in the same DB or a small dedicated KV).
- The widget can determine a `default_country` for phone parsing from the location it represents.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Customer enters phone the libphonenumber parser cannot resolve for the supplied country | Medium | Low (refused at widget) | Fail closed with a clear inline error; offer `+`-prefixed fallback |
| Contact-creation 409 returns and refetch finds no matching record (race lost but writer still in flight) | Low | Medium (one retry needed) | Bounded retry with backoff; surface after 3 attempts |
| Session close threshold lower than Podium's actual expiry leaves margin too thin | Low | Medium (customer surprised) | Tunable in `config/settings.yaml`; instrumented with metrics |
| Multi-location embed snippet config mistake routes a whole store wrong | Medium | High (operational impact) | Reject at handler; alarm on > N rejections in M minutes |
| Opt-out store outage leaves all outbound blocked or all permitted | Low | High (compliance OR availability) | Cache with short TTL + fail-closed on outage (block, don't permit) |
| Phone library upgrade changes parser behavior on edge cases | Low | Low | Pin major version; integration test suite covers AU + US + UK |

## Educational Disclaimer

This skill ships production-grade webchat-handler patterns for the Podium API as of the date the skill was authored. Podium's webchat session expiry, attachment size limit, and per-location routing semantics may evolve. Validate the specific timeouts, size limits, and endpoint URLs against the Podium developer documentation before deploying. Messaging-compliance rules (TCPA in the US, the Spam Act in Australia) are jurisdiction-specific; the opt-out propagation logic here is necessary but not sufficient for compliance — consult counsel for your specific obligations.
