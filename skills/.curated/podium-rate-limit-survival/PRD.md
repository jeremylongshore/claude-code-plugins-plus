# PRD: Podium Rate Limit Survival

## Summary

**One-liner**: Production-grade rate-limit survival layer for Podium API integrations — token-bucket pacing, `Retry-After` parsing, daily-quota monitoring, per-endpoint bucket isolation, end-of-day burst smoothing, and webhook amplification admission control.

**Domain**: SaaS integration / API rate limiting / SMB customer-engagement platforms

**Users**: Integration engineers, SaaS platform engineers, agency operators running burst-prone Podium integrations (review requests, webhook fan-out)

## Problem Statement

The Podium API enforces both a per-minute envelope (documented at 60 req/min per OAuth app) and a silent 24-hour envelope. Naive integrations hit six distinct failure modes — retry-on-429 cascades that consume the daily quota by lunch, ignored `Retry-After` server hints, daily-quota breaches that fire on Friday afternoons, per-endpoint contagion when one bucket exhausts and crashes siblings, end-of-day review-request bursts that drop 30-50% of writes, and inbound-webhook amplification that turns a 100-event burst into 500 outbound calls.

The Podium SDKs do not address any of these. Customer support handles them after the fact, after review-request automation has missed its 5pm window and lost a day of customer-engagement signal. This skill installs the rate-limit-survival layer that prevents each failure mode by construction.

## Target Users

### Persona 1: Integration Engineer (Ravi)

- **Role**: Builds and operates the outbound Podium API layer of a webhook-driven integration.
- **Goals**: Zero 429-induced data loss; bursts process at 100% success rate even when 50% slower; quota consumption is observable, not discovered.
- **Pain Points**: A 5pm review-request burst silently dropped 40% of writes last Friday and the customer noticed before he did. The retry loop he inherited from a previous engineer cascades on 429s and ate the daily quota by 11am during a Shopify flash sale.
- **Technical Level**: High (asyncio fluent, comfortable with token-bucket math, has run production systems).

### Persona 2: Agency Operator (Mei)

- **Role**: Operates a single platform service that fans out to 50+ client Podium organizations.
- **Goals**: One client's burst cannot blow the quota for another; per-endpoint isolation is visible in dashboards; daily-quota alerts route by client.
- **Pain Points**: A single chatty client's `conversations.write` endpoint exhausted the per-minute window and another client's `contacts.read` started 429-ing. No tooling existed to see the cross-contamination.
- **Technical Level**: Medium-High (ops-engineer profile; reads code, prefers playbooks and dashboards).

### Persona 3: Site Reliability Engineer (Jordan)

- **Role**: On-call for a Podium-integrated service. Does not own the integration code but must respond when a 429 cascade fires at 4:55pm AEST.
- **Goals**: A runbook short enough to execute under stress; clear page tiers (warn → page → throttle); a verifiable indicator that the quota will not breach.
- **Pain Points**: Previous cascades took 90 minutes to recover because the team had no kill-switch for the offending endpoint family.
- **Technical Level**: Medium (executes runbooks; does not build them).

## User Stories

### US-1: Token-bucket pacing (P0)

**As** an integration engineer,
**I want** outbound Podium calls paced by an in-process token bucket sized to the documented 60 req/min ceiling,
**So that** burst traffic queues rather than 429-cascades, and no retry storm is possible by construction.

**Acceptance Criteria:**

- Token bucket sized at 60 req/min with configurable burst capacity (default 10)
- Concurrent callers serialize on `bucket.acquire()` — no thundering herd
- Bucket sleeps outside the internal lock so refill timing is correct under concurrency
- The bucket is the *only* place rate is enforced — no `time.sleep(0.1)` sprinkles in the call sites

### US-2: `Retry-After` parsing (P0)

**As** an integration engineer,
**I want** `Retry-After` parsed correctly for both integer-seconds and HTTP-date forms,
**So that** residual 429s back off by the server's actual hint, not a guess.

**Acceptance Criteria:**

- Parser accepts integer seconds (`Retry-After: 30`) and HTTP-date (`Retry-After: Wed, 09 May 2026 17:00:00 GMT`)
- Malformed headers fall back to a safe default (60s), never crash
- Wait is capped at 120s to prevent a misconfigured server from pinning the integration indefinitely

### US-3: Daily quota monitor (P0)

**As** an SRE,
**I want** to be paged before the 24-hour quota envelope breaches,
**So that** I can engage throttling during business hours, not at 11pm on Friday.

**Acceptance Criteria:**

- Counter increments atomically per outbound call (Redis INCR or SQLite UPDATE)
- TTL is set to UTC midnight + 1h grace on first increment of the day
- Three severity tiers fire at 70% (warn), 85% (page), 95% (throttle)
- Throttle tier drops the token-bucket rate by 50% automatically until UTC midnight

### US-4: Per-endpoint bucket isolation (P1)

**As** an agency operator,
**I want** separate buckets per endpoint family (conversations, contacts, reviews, locations, webhooks),
**So that** one endpoint exhausting its slice cannot 429-cascade onto siblings.

**Acceptance Criteria:**

- Per-family buckets sized so sum-of-rates = 60 req/min (the documented ceiling)
- Endpoint family extracted from the path (`/v4/conversations/...` → `conversations`)
- Unknown families fall through to a default bucket — never to a global free-for-all
- Per-family consumption visible in the daily-quota monitor's structured logs

### US-5: End-of-day burst smoother (P1)

**As** an integration engineer for KombiLife (5pm AEST review-request cluster),
**I want** the 80-request burst smoothed over a 120-second window,
**So that** 100% of review requests succeed, with the trade-off being a 2-minute (instead of 30-second) processing window.

**Acceptance Criteria:**

- `BurstSmoother.submit_batch()` accepts a list of requests + a handler coroutine
- Per-request delay is `max(target_window/N, 1/bucket_rate)` — bucket rate dominates on small N
- Submits sequentially with the computed delay, awaiting the bucket each call
- Returns the list of results in original order

### US-6: Webhook amplification admission control (P1)

**As** an integration engineer,
**I want** inbound webhooks scored by their outbound amplification factor and rejected when projected cost exceeds 5% of remaining daily budget,
**So that** a burst of high-amplification events cannot collapse the daily quota in a single minute.

**Acceptance Criteria:**

- Configurable amplification factor map per inbound event type
- Admission denies when projected cost > 5% of remaining daily quota
- Denials log a structured event for capacity planning
- For Podium-delivered webhooks, denial → non-2xx response triggers Podium's own retry (acceptable)
- For non-replayable webhooks (Shopify), denial → durable queue spill (responsibility of caller; this skill does not provide the queue)

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Token bucket must serialize concurrent acquisitions correctly under asyncio (sleep outside lock) |
| REQ-2 | `Retry-After` parser must accept both RFC 7231 forms and fall back safely on malformed input |
| REQ-3 | Daily quota counter must be atomic (Redis INCR) and TTL-set on first daily increment |
| REQ-4 | Daily quota monitor must emit three severity tiers (warn/page/throttle) with structured logs |
| REQ-5 | Per-endpoint buckets must sum to the documented per-minute ceiling — no over-allocation |
| REQ-6 | Burst smoother must respect both target window and bucket rate, whichever is slower |
| REQ-7 | Admission controller must compute cost against *remaining* daily budget, not absolute quota |
| REQ-8 | All retry waits must be capped (default 120s) to prevent indefinite stalls |
| REQ-9 | Throttle mode must reduce bucket rate by 50% and remain in effect until UTC midnight |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/*` | * | Every outbound call passes through the bucket — no exceptions |
| Redis | INCR / EXPIRE / GET | Daily-quota counter store |
| Local SQLite (fallback) | UPDATE / SELECT | Daily-quota counter when Redis unavailable |

## Non-Goals

- This skill does not implement OAuth2 token caching — that is `podium-auth`.
- This skill does not implement webhook signature verification — that is `podium-webhook-reliability`.
- This skill does not provide a durable queue for spilled requests — callers integrate their own (SQS, RabbitMQ, Kafka).
- This skill does not retry permanent failures (4xx other than 429) — those surface to the caller immediately.
- This skill does not provide a dashboard UI — structured logs feed your existing observability stack.

## Success Metrics

| Metric | Target |
|---|---|
| Rate-limit-induced data loss per quarter | 0 |
| Per-minute 429 rate during burst windows | ≤ 0.5% (residual only; bucket prevents the rest) |
| Daily quota breach incidents per quarter | 0 (paged at 85%, throttled at 95%) |
| Cross-endpoint contagion incidents | 0 (per-family bucket isolation) |
| End-of-day review-request burst success rate | 100% (smoothed across 120s window) |
| Time to detect a 429 cascade | ≤ 60s (real-time bucket telemetry) |

## Constraints & Assumptions

- Podium's documented per-minute ceiling is 60 req/min per OAuth app. If Podium publishes a different number for your tier, override `rate_per_minute` accordingly.
- The 24-hour envelope is silent; default `DAILY_QUOTA` is conservative (50,000). Tune against observed traffic — Podium may grant you more or less.
- All clocks are UTC; the daily-quota TTL fires at UTC midnight, not local midnight. Operators in non-UTC regions must reason about which "Friday afternoon" the alert refers to.
- Redis is the preferred counter store; SQLite is acceptable for single-process deployments. The skill does not implement cross-process counter sharding without Redis.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bucket capacity over-tuned, allowing micro-bursts that 429 | Medium | Low | Default capacity = 10 (conservative); operators tune up after observing residual 429 rate |
| Daily quota counter race condition between INCR and EXPIRE | Low | Medium | First-write-wins on TTL — even with a race, the TTL is set on either branch |
| Per-family rate sum > 60 req/min due to misconfiguration | High historically | Medium | Loader validates `sum(rates) <= 60` at startup; fails loudly on mismatch |
| `Retry-After` HTTP-date form encounters a parser the engineer didn't expect | Low | Low | Two parsers tried; fall back to 60s default; never crashes |
| Burst smoother queues too aggressively and blocks foreground task | Medium | Medium | Smoother is async; foreground task can `await` it with a timeout |
| Admission denial floods logs during a legitimate burst | Medium | Low | Log denials at WARN, not ERROR; aggregate counts in structured fields |
| Redis outage takes out the daily-quota monitor | Medium | Medium | Fall back to local SQLite counter; quota monitor degrades gracefully, never crashes |

## Educational Disclaimer

This skill ships production-grade rate-limiting patterns for the Podium API as of the date the skill was authored. Rate-limit policies evolve; the documented 60 req/min ceiling may change. Validate the specific per-minute and per-day envelopes against the Podium developer documentation before deploying. The skill author is not responsible for breaking changes in upstream Podium rate-limit behavior.
