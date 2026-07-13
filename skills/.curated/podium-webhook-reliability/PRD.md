# PRD: Podium Webhook Reliability

## Summary

**One-liner**: Production-grade webhook receiver layer for Podium integrations — HMAC-SHA256 signature verification on the raw body, replay-attack protection via timestamp + nonce window, idempotent dedup with 24h TTL matched to Podium's retry ceiling, dead-letter queue with multiple backend options, ordered batch dispatch, and constant-time signature comparison.

**Domain**: SaaS integration / webhook receivers / event-driven SMB customer-engagement platforms

**Users**: Integration engineers, security engineers, on-call SREs operating Podium-integrated services that receive call transcripts, webchat events, conversation lifecycle events, and review notifications.

## Problem Statement

Podium delivers webhooks to receiver endpoints over HTTPS with an HMAC-SHA256 signature header, retries on 5xx for up to 24 hours, and can batch multiple events in a single delivery. Naive receivers fail in six distinct ways under production load — forged events from attackers who learn the URL, replay attacks against stateless handlers, duplicate processing from Podium's aggressive retry policy, lost events when handlers raise and exhaust retries, out-of-order processing within and across batches, and timing-attack-recoverable signature compares.

These failures are silent until a customer notices. A campervan retailer with two locations runs an AI phone system whose context-window cost is metered per call transcript ingest; a duplicate-processed transcript double-charges the AI inference. A forged review notification can prompt the ops team to respond to a customer who never wrote the review. The off-the-shelf Podium SDKs do not address any of these failure modes. This skill installs the production-engineering layer that prevents each failure mode by construction.

## Target Users

### Persona 1: Integration Engineer (Ravi)

- **Role**: Builds and operates a Podium webhook receiver that ingests call transcripts, webchat events, and review notifications for a single SMB.
- **Goals**: Zero forged events processed; zero duplicate side effects; every failed event recoverable from the DLQ; batch-ordering edge cases handled by construction not by post-incident patches.
- **Pain Points**: The previous receiver accepted any POST and a contractor's penetration test created 200 phantom contacts in 3 minutes; the retry storm during a Redis outage processed every call transcript five times and exhausted the AI context budget for the day.
- **Technical Level**: High (FastAPI/asyncio fluent, has shipped HMAC verification before, comfortable with Redis idempotency patterns).

### Persona 2: Security Engineer (Priya)

- **Role**: Reviews and signs off on the webhook integration before it goes to prod. Owns the threat model for inbound side-channel traffic.
- **Goals**: Constant-time HMAC compare; replay window enforcement; secret stored in a real secret store with rotation policy; audit trail for every rejected signature; no logging of request bodies for failed signatures (attacker probing).
- **Pain Points**: Previous integrations used `==` for signature compare; a junior engineer caught it in review but only because they happened to remember the timing-attack class. There is no automated guard.
- **Technical Level**: High (threat-modeling background, fluent in OWASP API Top 10, comfortable arguing with developers about provably-safe primitives).

### Persona 3: On-Call SRE (Jordan)

- **Role**: On-call for the Podium-integrated service. Does not own the receiver code but must respond when it pages at 2am.
- **Goals**: A runbook for draining the DLQ after a handler bug is patched; clear signal on whether Podium-side or receiver-side is the root cause; ability to replay events without re-firing the ones that already succeeded.
- **Pain Points**: Previous outages required `grep`-ing log archives for raw payloads because there was no DLQ; replays double-fired half the events because there was no dedup cache covering replays.
- **Technical Level**: Medium (executes runbooks; comfortable with `redis-cli` and `curl`).

## User Stories

### US-1: HMAC-SHA256 signature verification on the raw body (P0)

**As** an integration engineer,
**I want** every inbound webhook verified against the signing secret using HMAC-SHA256 over the raw request body,
**So that** forged POSTs are rejected with 401 before any handler logic runs.

**Acceptance Criteria:**

- Signature is computed over the raw bytes of the body, never the re-encoded JSON.
- Missing signature header returns 401 without parsing the body.
- Invalid signature returns 401; the body is NOT logged (attacker probing).
- Verification uses `hmac.compare_digest`, never `==`.

### US-2: Replay-attack window enforcement (P0)

**As** a security engineer,
**I want** every event's signed timestamp checked against a 5-minute window,
**So that** an attacker replaying a captured-off-the-wire signed event cannot keep firing it forever.

**Acceptance Criteria:**

- Window is configurable (default 300 seconds).
- Both past-skew and future-skew are bounded by the window.
- Failed window check returns 401 (same response code as signature failure — does not leak the difference).

### US-3: Idempotent dedup with 24h TTL (P0)

**As** an integration engineer,
**I want** every event_id atomically claimed in Redis with a 24-hour TTL,
**So that** Podium's retry-on-5xx for up to 24 hours never causes a duplicate side effect.

**Acceptance Criteria:**

- Claim uses `SET NX EX 86400` (atomic check-and-set).
- Duplicate event returns 200 with `status: "duplicate"` — Podium stops retrying.
- TTL is exactly 86400 seconds (24h Podium retry ceiling).
- In-memory fallback exists for dev when Redis is unavailable.

### US-4: Dead-letter queue persistence before 5xx (P0)

**As** an on-call SRE,
**I want** every handler exception to persist the raw signed payload to a DLQ before the response returns 5xx,
**So that** I can replay the event after the handler bug is fixed, independent of Podium's retry clock.

**Acceptance Criteria:**

- DLQ entry contains raw body, signature header, event_id, exception class + message, received_at timestamp.
- DLQ persist happens before the response is sent — failure to persist is itself logged and paged.
- DLQ backend is pluggable: Redis list (default), SQLite, append-only JSONL.

### US-5: Batch event ordering by `occurred_at` (P1)

**As** an integration engineer,
**I want** events within a batch dispatched in `occurred_at` ascending order,
**So that** `conversation.deleted` never runs before `conversation.created` within a single delivery.

**Acceptance Criteria:**

- Batch sort uses `(occurred_at, event_id)` as the key for stable ordering.
- Cross-batch out-of-order events that violate a precondition are deferred to the DLQ with `reason: "out_of_order_*"`.
- Replay logic from the DLQ re-attempts deferred events after their precondition has been satisfied.

### US-6: Constant-time HMAC compare (P0)

**As** a security engineer,
**I want** signature comparison done with `hmac.compare_digest`,
**So that** the receiver does not leak the signature byte-by-byte via response latency.

**Acceptance Criteria:**

- All signature compares route through a single `verify_signature()` function.
- That function uses `hmac.compare_digest`, never `==`.
- A pre-commit grep gate fails the build if `==` appears within 3 lines of `hmac` or `signature` in source.

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | HMAC-SHA256 verification must run on raw bytes, before any JSON parse |
| REQ-2 | Signature compare must use `hmac.compare_digest` (constant-time) |
| REQ-3 | Replay window must be enforced (default 300s, configurable) |
| REQ-4 | Event dedup must use atomic `SET NX EX 86400` against the dedup backend |
| REQ-5 | Every handler exception must persist a DLQ entry before the 5xx is sent |
| REQ-6 | Batch events must be sorted by `(occurred_at, event_id)` before dispatch |
| REQ-7 | Out-of-order events that violate a precondition must defer to DLQ, not raise |
| REQ-8 | Webhook signing secret must be loaded from a secret store, never hardcoded |
| REQ-9 | Failed signature checks must NOT log the request body (attacker probing) |
| REQ-10 | The receiver must fail-closed: if Redis dedup is unreachable, return 503 |

## API Integrations

| Endpoint | Direction | Purpose |
|---|---|---|
| `POST /webhooks/podium` (your endpoint) | Inbound | Receive signed events from Podium |
| `https://api.podium.com/v4/conversations/{id}` | Outbound (handler) | Precondition checks for batch ordering |
| `https://api.podium.com/v4/contacts/{id}` | Outbound (handler) | Idempotent contact upsert (if applicable) |
| Redis `SET NX EX` / `LPUSH podium:dlq` | Sidecar | Dedup claim + DLQ persistence |

## Non-Goals

- This skill does not implement OAuth2 authentication for outbound Podium API calls — that is `podium-auth`'s responsibility.
- This skill does not implement the application-level handlers themselves (contact upsert, transcript ingest, review notification) — those are downstream skills like `podium-call-transcript-pipeline`, `podium-webchat-handler`, `podium-review-request-automation`.
- This skill does not implement webhook **outbound** delivery (your service emitting events to other systems) — that is a separate engineering surface with a different threat model.
- This skill does not provide a UI for inspecting the DLQ — the CLI tools cover the operator workflow.

## Success Metrics

| Metric | Target |
|---|---|
| Forged-event acceptance rate | 0 (constant-time + signed-payload verify) |
| Duplicate handler invocations per `event_id` | ≤ 1 over any 24h window |
| Events lost without a DLQ entry | 0 (DLQ persist precedes 5xx response) |
| Out-of-order events that violate a precondition reaching handler logic | 0 (deferred to DLQ instead) |
| Time-to-replay after handler fix (DLQ drain) | < 30 minutes for 10,000 events at default rate |
| Mean signature-verify latency | < 5 ms per request (HMAC-SHA256 + window check) |

## Constraints & Assumptions

- Podium's signature header format is assumed to be `t=<unix_ts>,v1=<hex_hmac>` (Stripe-style). Verify against current Podium docs at integration time and adjust the parser if the format differs.
- Podium's webhook retry policy is 24 hours of exponential backoff on 5xx; the dedup TTL is matched to this ceiling. If Podium changes the policy, the TTL must move with it.
- Event IDs are assumed to be globally unique. If Podium reuses IDs across event types, the dedup key must include the type prefix (the skill already namespaces under `podium:evt:`).
- Redis is the default dedup backend because it provides the atomic `SET NX EX` primitive cheaply. SQLite + in-memory fallbacks exist for dev but are not recommended for prod.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Webhook signing secret leaked in commits | Medium | Critical (forgery possible) | `.gitignore` audit + grep gate; SOPS at rest in prod |
| Redis dedup outage causes duplicate processing | Low-Medium | High (double-charged AI calls, double contact writes) | Fail-closed to 503 — handler refuses without dedup |
| DLQ persistence fails silently | Low | Critical (event loss) | DLQ persist must succeed before 5xx; persist failures page on-call |
| Timing-attack on signature compare | Low (with `compare_digest`) | Critical (signature recovery) | Single verify function; pre-commit grep gate |
| Out-of-order batch events corrupt downstream state | Medium | Medium | Sort within batch; defer on precondition fail |
| Replay window too tight causes legitimate-event rejection from clock skew | Low | Medium (legitimate events lost) | 300s default; configurable; NTP-synced receiver hosts |

## Educational Disclaimer

This skill ships production-grade webhook-reliability code patterns for the Podium API as of the date the skill was authored. Webhook delivery semantics, retry policies, signature header formats, and event schemas evolve. Validate the specific header name, signature format, retry ceiling, and event ID field against the Podium developer documentation before deploying. The skill author is not responsible for breaking changes in upstream Podium behavior.
