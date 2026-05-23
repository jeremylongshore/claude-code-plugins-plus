# PRD: Podium Auth

## Summary

**One-liner**: Production-grade OAuth2 authentication layer for Podium integrations — token caching, refresh-token rotation persistence, 90-day decay monitoring, scope-drift detection, multi-tenant credential routing, and dual-credential rotation runbook.

**Domain**: SaaS integration / API authentication / SMB customer-engagement platforms

**Users**: Integration engineers, agency operators, SaaS platform engineers building on the Podium API

## Problem Statement

The Podium API uses OAuth2 with rotating refresh tokens, a 90-day non-use decay clock, and per-organization scopes. Naive integrations break in six distinct ways under production load — token expiry storms when a burst notices expiry simultaneously, silent rotation drift when the new refresh token is lost on a crash, dead credentials after a quiet season, 403s after an admin re-grants the app with reduced scopes, leaked client secrets in commits, and downtime cascades when on-call rotates a credential without a dual-credential window.

The off-the-shelf Podium SDKs do not address any of these failure modes. Customer support handles them post-incident, after data has been lost or sent to the wrong organization. This skill installs the production-engineering layer that prevents each failure mode by construction.

## Target Users

### Persona 1: Integration Engineer (Ravi)

- **Role**: Builds and operates a Podium-integrated webhook handler that ingests call transcripts, webchat messages, and review events for a single SMB.
- **Goals**: Zero auth-induced incidents; the integration is invisible operationally; the on-call playbook for rotating a leaked secret is one page long.
- **Pain Points**: Refresh token died over the long weekend; a previous engineer pasted the client_secret into a `.env.example`; the integration silently dropped 4 days of webhooks while the access token loop spun on 401.
- **Technical Level**: High (OAuth2 fluent, comfortable with async Python / Node, has run production systems before).

### Persona 2: Agency Operator (Mei)

- **Role**: Manages Podium for 50+ client organizations from a single platform service.
- **Goals**: Per-org credential isolation; one client's credential failure does not affect any other; bulk onboarding of a new org takes 5 minutes, not 5 hours; audit trail of which credential was used for which write.
- **Pain Points**: A single `PODIUM_TOKEN` env var means a wrong-org request silently writes to the wrong location's contacts; rotating one client's credential brings the whole service down.
- **Technical Level**: Medium-High (ops-engineer profile; reads code, prefers playbooks).

### Persona 3: Site Reliability Engineer (Jordan)

- **Role**: On-call for a Podium-integrated service. Does not own the integration code but must respond when it pages at 2am.
- **Goals**: A runbook short enough to execute under stress; clear page severity (warn vs page vs hard-fail); a verifiable health check after every rotation.
- **Pain Points**: Previous rotations took the service down because the old secret was revoked before the new one was deployed.
- **Technical Level**: Medium (executes runbooks; does not build them).

## User Stories

### US-1: Proactive token refresh (P0)

**As** an integration engineer,
**I want** the access token to be refreshed at 80% of TTL behind a single-flight lock,
**So that** burst traffic does not stampede the token endpoint and the integration never serves a 401 from an expired token.

**Acceptance Criteria:**

- Refresh fires when token age ≥ 80% of `expires_in`
- Concurrent callers serialize on one `_refresh()` call (no thundering herd)
- Token endpoint receives at most 1 refresh request per (org, TTL window)
- On refresh failure, the cached token is retained until expiry — fail-open on transient errors

### US-2: Refresh-token rotation persistence (P0)

**As** an integration engineer,
**I want** the new refresh token persisted to the secret store atomically inside the refresh call,
**So that** a process crash mid-refresh never leaves the system with a dead refresh token.

**Acceptance Criteria:**

- New refresh token is written via temp-file-then-rename (atomic on POSIX)
- Persistence happens before `_cached` is updated — if persist fails, the refresh is aborted
- Old refresh token remains valid only until the next successful refresh completes

### US-3: 90-day decay monitoring (P0)

**As** an SRE,
**I want** to be paged before the refresh token decays,
**So that** I can trigger user re-authorization during business hours, not at 3am.

**Acceptance Criteria:**

- Warn log at age ≥ 60 days
- Page on-call at age ≥ 75 days
- Hard-fail (raise) at age ≥ 85 days with explicit re-auth instructions in the error message

### US-4: Scope drift detection (P1)

**As** an integration engineer,
**I want** scopes validated on every refresh,
**So that** an admin re-grant with reduced scopes fails loudly at refresh time, not silently on the next 403.

**Acceptance Criteria:**

- A `REQUIRED_SCOPES` set is defined at module init
- Refresh response is parsed for `scope` field, split on whitespace
- Any missing required scope raises `PodiumAuthError` with the explicit missing-scopes list

### US-5: Multi-tenant credential router (P1)

**As** an agency operator,
**I want** per-organization `PodiumAuth` instances with isolated caches,
**So that** one client's auth failure cannot affect another client's traffic and the router can verify the org slug before issuing a token.

**Acceptance Criteria:**

- `PodiumOrgRouter` keyed by org slug
- Each org has independent token cache, single-flight lock, and decay state
- Unknown org slug raises `KeyError` immediately — no fallback to a default credential

### US-6: Dual-credential rotation (P1)

**As** an SRE,
**I want** a runbook that overlaps old and new credentials,
**So that** in-flight webhook handlers complete on the old credential while new requests start using the new one.

**Acceptance Criteria:**

- Runbook is committed to the repo (not a wiki link)
- Rotation requires a verified health-check call before the old credential is revoked
- Rollback path documented if health check fails

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Token cache must be single-flight (one refresh per cache miss across concurrent callers) |
| REQ-2 | Refresh must persist the new refresh token atomically before returning |
| REQ-3 | Decay monitor must emit at three severity levels: warn (60d), page (75d), hard-fail (85d) |
| REQ-4 | Scope validation must run inside `_refresh()` before assigning `_cached` |
| REQ-5 | Multi-tenant router must reject unknown org slugs with `KeyError`, not fall back to a default |
| REQ-6 | All credentials must be loaded from a secret store, never hardcoded in source |
| REQ-7 | Rotation runbook must include a health-check step before old-credential revocation |
| REQ-8 | All HTTP calls to Podium auth must have a timeout (default 10s) and exponential backoff on 5xx |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://accounts.podium.com/oauth/authorize` | GET | Initial user authorization flow (browser redirect) |
| `https://accounts.podium.com/oauth/token` | POST | Exchange authorization code for refresh token; refresh access token |
| `https://api.podium.com/v4/me` | GET | Verify a credential is live (used in rotation health check) |
| `https://accounts.podium.com/oauth/revoke` | POST | Revoke a refresh token on rotation completion |

## Non-Goals

- This skill does not implement the initial authorization-code flow (one-time browser redirect handled by the operator manually).
- This skill does not handle Podium's webhook signature verification (covered by `podium-webhook-reliability`).
- This skill does not implement org-level RBAC inside the agency router — that is the calling application's responsibility.
- This skill does not provide a UI for credential management — it is a library + scripts, not a console.

## Success Metrics

| Metric | Target |
|---|---|
| Auth-induced incidents per quarter | 0 |
| Token endpoint requests per access-token TTL window | ≤ 1 per org |
| Median time-to-detect refresh-token decay | ≥ 15 days before hard-fail |
| Mean time-to-rotate a leaked secret (page → revoke) | ≤ 30 minutes with zero dropped requests |
| Scope-drift incidents that reach production traffic | 0 (caught at refresh time) |

## Constraints & Assumptions

- Podium's OAuth2 implementation rotates the refresh token on every refresh (verified against current docs; if this changes, REQ-2 simplifies).
- Refresh-token decay is 90 days of non-use; numeric thresholds (60/75/85) are conservative against that ceiling.
- Token endpoint enforces rate limits but does not document the exact threshold — the single-flight lock makes the integration robust to whatever the limit is.
- Operators have a secret store available; this skill does not implement one.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Refresh-token persistence loses the new token on crash | Low | High (dead credential) | Atomic temp-file-then-rename; persist before updating cache |
| Decay monitor misses a token (page is swallowed) | Medium | High (silent expiry) | Three severity levels; hard-fail at 85d forces visible failure |
| Multi-tenant router routes to wrong org due to slug typo | Medium | High (data written to wrong location) | Unknown slug → `KeyError`, never a fallback |
| Rotation drops in-flight webhooks | Medium | Medium (data loss for replays) | Dual-credential overlap window; queue drain before revoke |
| Client secret leaked in git | High historically | Critical | `.gitignore` audit + grep gate in pre-commit; SOPS at rest in prod |

## Educational Disclaimer

This skill ships production-grade authentication code patterns for the Podium API as of the date the skill was authored. OAuth2 implementations evolve. Validate the specific TTLs, scope strings, and endpoint URLs against the Podium developer documentation before deploying. The skill author is not responsible for breaking changes in upstream Podium behavior.
