# PRD: Podium Multi-Location Router

## Summary

**One-liner**: Production-grade multi-location dispatch layer for Podium integrations — per-location credential isolation, pre-flight `location_uid` verification, immutable JSONL audit trail, idempotent bulk onboarding, and per-location rate-limit budgets that cannot starve each other.

**Domain**: SaaS integration / multi-tenant routing / SMB customer-engagement platforms / agency operations

**Users**: Agency operators managing many Podium accounts, multi-store SMBs running 2+ physical locations, compliance auditors needing per-location attribution.

## Problem Statement

Podium's data model has two tenancy layers: **organizations** (the OAuth boundary) and **locations** (the physical-store boundary). The Podium API does not enforce that a write targeted at `location_uid=X` actually went to the location the operator intended — any well-formed UID the token has access to is accepted. Integrations built without an explicit routing layer fail in six distinct ways under production load: writes silently land at the wrong location, Sydney's credential is reused for a Burleigh Heads write, the audit log cannot answer "which location received this?", bulk onboarding leaves dangling half-records on partial failure, location-ownership verification is skipped before write, and a shared rate-limit bucket lets one location burn quota the others need.

The off-the-shelf Podium SDKs treat `location_uid` as just another query parameter. They do not isolate credentials per location, do not pre-flight-verify ownership, do not emit a routing audit trail, and do not size rate-limit buckets per location. This skill installs the routing layer that makes wrong-location writes structurally impossible.

## Target Users

### Persona 1: Agency Operator (Mei)

- **Role**: Manages Podium for 50+ client organizations from a single platform service. Each client has 1–8 physical locations.
- **Goals**: Per-location credential isolation across hundreds of locations; bulk onboarding a new agency client takes 10 minutes, not 4 hours; a customer dispute can be traced to the exact location, credential, and request in one query.
- **Pain Points**: A previous engineer used a single shared OAuth token across the whole agency; a wrong-org request silently wrote a customer's data to the wrong client's location and the agency only discovered it when the wrong client received a refund email.
- **Technical Level**: Medium-High (ops-engineer profile; reads code, prefers playbooks and runbooks).

### Persona 2: Multi-Store Owner (Mark, the KombiLife archetype)

- **Role**: Owns and operates 2 physical locations (Sydney + Burleigh Heads). One operations manager covers both; one shared Podium org but two real-world stores with different staff, hours, and review-request cadences.
- **Goals**: Sydney's holiday review-request burst does not break Burleigh Heads' webchat. Sydney's staff cannot accidentally send a review request from a customer who visited the other store.
- **Pain Points**: Last December Sydney sent 800 review requests in 3 hours and Burleigh Heads' webchat returned 429s for the rest of the afternoon. The Burleigh Heads manager spent the evening troubleshooting an integration that was not broken — Sydney had just burned the shared quota.
- **Technical Level**: Low-Medium (owner-operator; consumes the integration, does not build it; the integration was built by an external consultant who needs the right defaults to ship).

### Persona 3: Compliance Auditor (Priya)

- **Role**: Reviews data-processing trails for SMB platforms subject to GDPR / CCPA / state PII regulations. Walks into the integration cold, needs the audit trail to be self-explanatory.
- **Goals**: For any customer-data write, answer in one query: which physical location received the data, which credential authorized the call, when, and from what request ID. Six-month retention minimum.
- **Pain Points**: Previous platforms had "we'll check the logs" answers that took two weeks and still could not attribute writes to specific locations because the integration used a single org-scoped credential and logged only the org UID.
- **Technical Level**: High on the regulatory side, Medium on the technical side (reads logs, runs simple queries, does not modify the integration).

## User Stories

### US-1: Per-location credential isolation (P0)

**As** an agency operator,
**I want** each location to have its own `PodiumAuth` instance keyed by `location_uid`,
**So that** Sydney's auth state is structurally separate from Burleigh Heads', even when both locations share the same underlying OAuth app at the org level.

**Acceptance Criteria:**

- `LocationRouter` is keyed by `location_uid`, never by `org_slug`
- Two locations under the same org get two separate `PodiumAuth` instances with distinct refresh-token-file paths
- An auth failure on one location does not affect any other location's auth state
- The map is loaded from a credentials file (or AWS / GCP / SOPS secret store) at startup

### US-2: Pre-flight location verification (P0)

**As** an integration engineer,
**I want** the router to verify a `location_uid` is in scope before any write,
**So that** a stale or wrong UID raises loudly instead of producing a silent wrong-location write.

**Acceptance Criteria:**

- Before any call, the router checks `location_uid` against the set returned by `GET /v4/locations`
- The verification result is cached with a 1-hour TTL (configurable)
- A `location_uid` not in the set raises `LocationNotInScopeError` with the list of in-scope UIDs
- Re-verification under load is single-flight (one verify call per location per TTL window)

### US-3: Structured audit trail (P0)

**As** a compliance auditor,
**I want** every API call to emit a JSONL record with `{ts, location_uid, org_slug, endpoint, method, status, request_id, latency_ms}`,
**So that** any compliance question about a specific customer's data write can be answered in one `audit_log_query.py` invocation.

**Acceptance Criteria:**

- One JSONL line per API call, append-only
- No tokens, request bodies, or PII fields are logged — routing fingerprint only
- `request_id` is generated by the client wrapper and included in any error surface for cross-correlation
- The query script supports filtering by `location_uid`, date range, and status

### US-4: Idempotent bulk onboarding (P1)

**As** an agency operator,
**I want** to onboard 5+ new locations in one operation with safe resumption after partial failure,
**So that** a half-completed onboarding does not leave dangling credential records that cause later operations to crash or fall through.

**Acceptance Criteria:**

- `onboard_locations()` processes one location at a time; failure on one does not abort the rest
- Per-location atomic invariant: credential record + auth instance + verification all succeed, or all are rolled back
- Re-running with the same input is safe — already-onboarded locations are detected and marked `skipped_existing`
- Final summary lists `{onboarded, skipped_existing, failed}` counts with per-location detail

### US-5: Per-location rate-limit isolation (P1)

**As** a multi-store owner,
**I want** each location to have its own token bucket sized to that location's expected traffic,
**So that** one location's burst cannot starve another location's webchat or review-request flow.

**Acceptance Criteria:**

- One `TokenBucket` instance per `location_uid`
- Bucket capacity and refill rate are read from `config/settings.yaml`; defaults are conservative
- A burst at one location does not affect any other location's bucket
- 429 responses from Podium are surfaced as `LocationRateLimitExceeded` with the source location_uid

### US-6: Unknown-location refusal (P0)

**As** an integration engineer,
**I want** the router to raise `UnknownLocationError` immediately for a `location_uid` not in the credentials map,
**So that** a missing or typo'd UID cannot fall through to a default credential or "best guess" route.

**Acceptance Criteria:**

- `router.get_client("not-in-map")` raises `UnknownLocationError` with explicit remediation
- There is no default credential, no fallback location, no "first registered" tie-breaker
- The error message names `onboard_location.py` as the recovery path

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Router map is keyed by `location_uid`; map operations never use `org_slug` as a key |
| REQ-2 | `ensure_location_verified()` calls `GET /v4/locations` at most once per location per `VERIFY_TTL_SECONDS` window |
| REQ-3 | Audit log writes are append-only JSONL with a fixed schema; no tokens or PII |
| REQ-4 | `onboard_locations()` is idempotent: re-running with the same input never duplicates entries |
| REQ-5 | Each `location_uid` has its own `TokenBucket`; buckets do not share state |
| REQ-6 | `UnknownLocationError` is raised for any unknown `location_uid` — no fallback path exists |
| REQ-7 | Partial-failure onboarding rolls back per-location to maintain the atomic invariant |
| REQ-8 | All HTTP calls to Podium have a default 10s timeout and propagate 429 / 5xx through the bucket / retry layer |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/locations` | GET | Enumerate locations the current token can write to (pre-flight verification) |
| `https://api.podium.com/v4/contacts` | POST / GET / PATCH | Write or read a contact at a specific `location_uid` |
| `https://api.podium.com/v4/conversations` | GET / POST | Webchat traffic — must be location-scoped |
| `https://api.podium.com/v4/review_invitations` | POST | Send a review request from a specific location |

All calls pass through `PodiumLocationClient.call()`, which inserts pre-flight verification + bucket acquisition + audit-log emission around the underlying HTTP request.

## Non-Goals

- This skill does not implement the OAuth flow — that is `podium-auth`'s domain. The router consumes `PodiumAuth` instances built upstream.
- This skill does not implement token-bucket internals — that is `podium-rate-limit-survival`'s domain. The router holds one bucket per location and delegates acquisition.
- This skill does not implement Podium webhook signature verification — that is `podium-webhook-reliability`'s domain.
- This skill does not provide a UI for credential or location management. It is a library + CLI scripts.
- This skill does not synchronize the location list from Podium back into the credentials map automatically — adding a new location remains an explicit `onboard_location.py` operation. Auto-sync would mask onboarding errors and is rejected by design.

## Success Metrics

| Metric | Target |
|---|---|
| Wrong-location writes per quarter | 0 |
| Audit log can answer "which location received this write?" in < 5 seconds | 100% of writes |
| Bulk onboarding success rate (≥ 5 locations in one operation) | ≥ 95% on first try, 100% after one retry |
| Per-location rate-limit isolation incidents (one location starves another) | 0 |
| Mean time-to-onboard a new location | ≤ 5 minutes including verification |
| Silent 403s on writes (location_uid not in scope) | 0 (pre-flight catches all) |

## Constraints & Assumptions

- Podium's location model: every customer-data write accepts a `location_uid` parameter; the API accepts any well-formed UID the token has access to without warning if the caller meant a different one.
- `GET /v4/locations` returns the set of UIDs the current token can see; this is the canonical scope check.
- A single OAuth app can be granted access to multiple locations under the same org. This skill treats them as separate routing keys regardless.
- Operators have a secret store (file, AWS, GCP, SOPS) for refresh tokens. This skill does not implement one — it consumes `podium-auth`'s persistence layer.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Wrong-location write due to stale `location_uid` lookup | High | High (data sent to wrong store) | Pre-flight verification against `/v4/locations` with 1h TTL |
| Credential cross-contamination across locations | Medium | High (audit-trail attribution wrong) | Per-`location_uid` `PodiumAuth` instance; no sharing |
| Audit log missing `location_uid` field | Low (fixed schema) | High (compliance unanswerable) | Schema enforced in library; integration tests assert schema |
| Bulk onboarding leaves dangling half-records | High historically | Medium (later operations crash on phantom location) | Per-location atomic invariant; rollback on any failure |
| Shared rate-limit bucket starves quiet locations | High | Medium (perceived outage at innocent location) | One bucket per `location_uid`; sized independently |
| Unknown `location_uid` falls through to default credential | Medium | Critical (silent wrong-org write) | `UnknownLocationError` raised; no default path exists |

## Educational Disclaimer

This skill ships production-grade routing code patterns for the Podium API as of the date the skill was authored. Podium's location model evolves; verify the specific endpoint paths (`/v4/locations`, `/v4/contacts`) and the `location_uid` field name against the Podium developer documentation before deploying. The skill author is not responsible for breaking changes in upstream Podium behavior or for incidents arising from misconfigured credential maps.
