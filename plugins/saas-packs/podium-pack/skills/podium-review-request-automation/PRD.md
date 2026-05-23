# PRD: Podium Review Request Automation

## Summary

**One-liner**: Production-grade automation for triggering Podium review requests from Shopify order events — cooldown enforcement, refund-race buffering, failed-send detection, review-response webhook ingestion, multi-platform routing validation, and unified opt-out compliance.

**Domain**: SaaS integration / e-commerce review pipelines / SMB customer-engagement / TCPA-adjacent compliance

**Users**: Marketing operations managers, e-commerce platform engineers, customer-success leads at multi-location merchants

## Problem Statement

Podium's review-request feature is the highest-ROI surface in the product — every well-timed request becomes a Google review that compounds local SEO. But the integration patterns published by Podium and Shopify do not address the six failure modes that cause merchant churn: requests sent during a recent-contact cooldown, requests fired before the refund window closes, silent carrier-side rejections, dropped review-response webhooks, multi-platform routing that lands on networks the customer doesn't use, and opt-out flags that don't propagate across flows.

A merchant whose review-request automation generates a TCPA complaint, a Podium account suspension, or a brand-damaging request to a refunded customer will churn. Worse, they will tell other merchants. This skill installs the production-engineering layer that prevents each of those failures by construction, with a defaulted-conservative posture: when in doubt, the system does not send.

## Target Users

### Persona 1: Marketing Operations Manager (Mark)

- **Role**: Owns the review-acquisition program at a multi-location SMB (KombiLife Australia — campervan rental, 4 locations, ~3,000 trips/month). Configures Podium campaigns, monitors review velocity, fields complaints.
- **Goals**: Maximize review volume without generating any complaints. Catch carrier failures within 24 hours so they can be retried via email. Have a single dashboard view of "did this customer get a request, did it land, did they respond."
- **Pain Points**: Last quarter, two customers received review requests inside the cooldown window (a known-bad customer experience). One review request fired to a customer mid-refund — the customer screenshotted it and posted to Trustpilot. A 1-star Google review hit before the team noticed because the webhook was dropped during a redeploy.
- **Technical Level**: Low-to-medium (configures campaigns, reads dashboards, opens tickets when something breaks — does not write code, but can describe failures precisely).

### Persona 2: E-commerce Platform Engineer (Priya)

- **Role**: Builds and operates the Shopify → Podium webhook bridge. Owns the cooldown store, the delayed-queue, the webhook signature verification.
- **Goals**: Idempotent webhook handling. Cooldown decisions that survive a process restart. Refund-status check at send-time, not just at schedule-time. Audit log of every sent/skipped decision so when Mark asks "why didn't this customer get a request" the answer is in a SQL query.
- **Pain Points**: Cooldown logic was originally in a per-process dict — restart wiped it. Refund check was originally at schedule-time only — the 5-day buffer was wasted. The original handler treated Podium's 200 response as proof of delivery and missed an 8% silent-failure rate.
- **Technical Level**: High (Python + Redis + Postgres fluent; has shipped production webhook bridges before).

### Persona 3: Customer-Success Lead (Devon)

- **Role**: Monitors review-response sentiment and escalates negatives. Owns the response-time SLA for 1-2 star reviews (their published commitment is 4 business hours).
- **Goals**: Zero dropped negative-review notifications. Slack page within 60s of a 1-star review arriving. Per-platform routing visibility (Google vs Facebook vs Podium-native) so the response is posted on the same surface.
- **Pain Points**: Discovered a 1-star Google review a week after it landed because the webhook receiver returned 500 during a deploy and Podium gave up after 3 retries. Has had to apologize to merchants whose response window was blown.
- **Technical Level**: Low (reads Slack, opens tickets; does not write code).

## User Stories

### US-1: Cooldown gate enforcement (P0)

**As** a marketing operations manager,
**I want** every review request to be blocked if the customer's phone received any prior Podium contact within the cooldown window,
**So that** customers never receive overlapping requests and we never trip Podium's spam-pattern suspension.

**Acceptance Criteria:**

- Cooldown state is keyed by normalized E.164 phone, not by `customer_id` (handles guest-checkout customers correctly)
- Default cooldown window is 30 days; configurable per-merchant
- `can_send()` returns `(allowed, seconds_remaining)` so the caller can log the remaining window
- Cooldown state survives process restart (Redis or SQLite, not in-memory dict)
- Concurrent webhook handlers cannot both pass the gate for the same phone in the same window

### US-2: Refund-race buffer (P0)

**As** a marketing operations manager,
**I want** review requests delayed by a configurable window after `orders/fulfilled`,
**So that** the customer has time to initiate a refund before the request fires, and refunded orders never produce a request.

**Acceptance Criteria:**

- Default buffer is 5 days from `fulfilled_at`; configurable per-merchant
- Buffer is implemented as a durable delayed queue (Redis streams / SQS / pgmq) — not `asyncio.sleep`
- At fire-time, the order's `financial_status` is re-checked; refunded / partially-refunded / voided / cancelled orders are silently skipped with a structured log event
- Opt-out is re-checked at fire-time — a contact who opts out during the buffer is suppressed

### US-3: Failed-send detection (P0)

**As** an e-commerce platform engineer,
**I want** every sent invitation tracked in an outbox keyed by `invitation_id`, reconciled against `review_invitation.delivered` and `review_invitation.failed` webhooks,
**So that** carrier-filtered sends are detected within 24 hours and the cooldown is rolled back so the customer is not falsely punished.

**Acceptance Criteria:**

- Outbox record created at API-call success, updated on each delivery webhook
- Records older than 24h in `sent` status (no terminal transition) are flagged for manual review
- On `failed`, the cooldown for the contact's phone is deleted (the customer never received the message)
- Outbox is persistent; survives process restart

### US-4: Idempotent review-response webhook handler (P0)

**As** a customer-success lead,
**I want** every `review.received` event to be processed exactly once and classified by sentiment,
**So that** 1-2 star reviews fire a Slack page within 60s and 4-5 star reviews route to a thank-you flow, with no duplicate fires from Podium's retry behavior.

**Acceptance Criteria:**

- Signature verified before processing (HMAC-SHA256 against `PODIUM_WEBHOOK_SECRET`)
- Event ID claimed via a 24h-TTL idempotency key before any side effect
- Sentiment classifier: rating ≤2 → escalate, rating ≥4 → thank, rating 3 → log-only
- Negative-review escalation publishes to a channel with delivery confirmation (not fire-and-forget)
- Handler returns 200 on duplicate events (do not 4xx — Podium would retry)

### US-5: Multi-platform routing validation (P1)

**As** a marketing operations manager,
**I want** the review-request destination platform validated against the customer's known accounts,
**So that** a Facebook-routed request never goes to a customer who has no Facebook account and silently produces a dead link.

**Acceptance Criteria:**

- `select_review_platform(customer, campaign)` returns the highest-confidence platform
- Order of preference: explicit customer preference → campaign default → Google fallback
- A Facebook-targeted campaign falls back to Google when the customer has no known `facebook_uid`
- Chosen platform is recorded on the invitation outbox record for post-hoc analysis

### US-6: Unified opt-out predicate (P0)

**As** a marketing operations manager,
**I want** opt-out enforcement to consult every opt-out signal (marketing SMS, review-flow, global unsubscribe, STOP-reply keyword) in a single predicate,
**So that** no customer who opted out of any flow ever receives a review request, regardless of which flow the opt-out came from.

**Acceptance Criteria:**

- `is_opted_out(phone)` consults at minimum 4 flags from the merged contact record
- Predicate is called at both schedule-time AND fire-time
- A STOP-reply from a non-review-flow Podium message triggers `podium_keyword_optout=true` and propagates to the source-of-truth contact record
- Audit CLI (`optout_compliance_audit.py`) can identify drift between flow-specific opt-outs and the unified flag

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Cooldown state must be keyed by E.164 phone and survive process restart |
| REQ-2 | Cooldown gate and opt-out predicate must both run at schedule-time AND fire-time |
| REQ-3 | Refund-race buffer must be a durable delayed queue, not an in-memory timer |
| REQ-4 | Every API send must produce an outbox record; outbox records resolve via `delivered` / `failed` webhooks |
| REQ-5 | On `review_invitation.failed`, the contact's cooldown must be rolled back |
| REQ-6 | `review.received` handler must verify HMAC signature before any side effect |
| REQ-7 | `review.received` handler must claim an idempotency key per event ID with 24h TTL |
| REQ-8 | Sentiment classification must escalate rating ≤2 to a channel with delivery confirmation |
| REQ-9 | Multi-platform routing must fall back to Google when the configured target is uncertain |
| REQ-10 | Opt-out predicate must consult ≥4 flags from the merged contact record |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/review-invitations` | POST | Create a review-request invitation for a contact |
| `https://api.podium.com/v4/contacts/{id}` | GET | Look up a contact's known platforms and opt-out flags |
| `https://api.podium.com/v4/contacts/{id}` | PATCH | Propagate STOP-reply opt-out across flows |
| Shopify `/admin/api/2024-04/orders/{id}.json` | GET | Re-check `financial_status` at fire-time |
| Shopify webhook `orders/fulfilled` | POST (inbound) | Trigger the schedule-time evaluation |
| Podium webhook `review_invitation.delivered` | POST (inbound) | Resolve outbox to `delivered` |
| Podium webhook `review_invitation.failed` | POST (inbound) | Resolve outbox to `failed`, roll back cooldown |
| Podium webhook `review.received` | POST (inbound) | Classify sentiment, route response |

## Non-Goals

- This skill does not implement Podium OAuth or token refresh — covered by `podium-auth`.
- This skill does not implement durable webhook persistence — covered by `podium-webhook-reliability`. The handlers here assume the queue/inbox is provided.
- This skill does not implement Podium rate-limit handling — covered by `podium-rate-limit-survival`. Sends here assume the calling layer respects per-campaign limits.
- This skill does not implement contact-record merging across Podium and Shopify — covered by `podium-contact-dedup`. The opt-out predicate consumes the merged record.
- This skill does not implement a campaign builder or merchant-facing UI — it is the back-end policy layer.
- This skill does not implement automated response-posting to negative reviews — it routes the notification; humans respond.

## Success Metrics

| Metric | Target |
|---|---|
| In-cooldown sends per quarter | 0 |
| Review requests fired to refunded orders per quarter | 0 |
| Silent carrier-rejection rate detected within 24h | ≥ 95% |
| Median time-to-detect a 1-star review (webhook to Slack) | ≤ 60s |
| Multi-platform route-misconfig sends per quarter | 0 |
| TCPA-related opt-out compliance incidents per year | 0 |

## Constraints & Assumptions

- Podium's `review_invitation.failed` webhook is the canonical signal for carrier-rejection — alternative methods (polling invitation status) are not used.
- The refund-race buffer is configurable per-merchant because product-line refund patterns differ (consumables vs durable goods).
- The cooldown window is configurable per-merchant because campaign cadence differs (a hotel may request review per stay; an e-commerce shop may request quarterly).
- Opt-out source-of-truth lives in the merged contact record produced by `podium-contact-dedup`.
- The integration runs in a single AWS region for any given merchant; multi-region cooldown state synchronization is out of scope.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cooldown bypass via guest-checkout phone variants | Medium | High (spam complaint) | Normalize to E.164 before keying; reject sends without a valid E.164 phone |
| Refund occurs after fire-time (post-send refund) | Medium | Medium (brand damage) | Cannot prevent; document explicitly that buffer protects against pre-send refunds only |
| `review_invitation.failed` webhook is itself dropped | Low | Medium (outbox stuck) | Periodic outbox sweep flags `sent` records older than 24h regardless of webhook |
| Opt-out propagation lags between flows | Medium | High (TCPA risk) | Unified predicate consults source-of-truth on every send; audit CLI detects drift |
| Sentiment classifier mis-routes a 3-star review | Low | Low (no action) | 3-star is log-only by design; ambiguity is acceptable |
| Multi-platform routing falls back to Google in error | Low | Low (Google reviews always render) | Conservative fallback is intentional; merchants prefer over-Google over no-review |

## Educational Disclaimer

This skill ships production-grade automation patterns for the Podium review-request feature as of the date the skill was authored. Podium's API surface, webhook contract, and Shopify's webhook payload schema evolve. Validate the specific field names (`financial_status`, `invitation_id`, `review.received`) against the current Podium and Shopify developer documentation before deploying. TCPA, Australian Spam Act, and equivalent regional regulations impose obligations beyond what this skill enforces — consult counsel for the compliance regime applicable to your jurisdiction. The skill author is not responsible for breaking changes in upstream Podium or Shopify behavior or for regional regulatory compliance.
