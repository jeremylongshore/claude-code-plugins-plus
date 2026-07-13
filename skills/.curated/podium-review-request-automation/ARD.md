# ARD: Podium Review Request Automation

## Architecture Pattern

**Webhook bridge + policy gate + durable outbox.** The skill ships a long-running HTTP service (`shopify_to_podium_bridge.py`) that ingests Shopify `orders/fulfilled` and Podium `review.*` webhooks, runs decisions through a policy gate (cooldown + opt-out + refund-status), schedules sends via a durable delayed queue, and reconciles delivery state via an outbox keyed by `invitation_id`. The CLIs (`cooldown_check.py`, `review_response_handler.py`, `optout_compliance_audit.py`) wrap the same internal modules for operator workflows.

Pattern: **Receive → gate → schedule → fire → reconcile, with every transition durable.** No in-memory state survives more than one HTTP request.

## Workflow

```
       ┌────────────────────────────┐
       │  Shopify webhook           │
       │  POST orders/fulfilled     │
       └─────────────┬──────────────┘
                     │ verify HMAC
                     ▼
       ┌────────────────────────────┐
       │  Policy gate (schedule-tm) │
       │  ├ normalize phone E.164   │
       │  ├ is_opted_out(phone)?    │ ── yes ─► log + drop
       │  └ cooldown.can_send()?    │ ── no  ─► log + drop
       └─────────────┬──────────────┘
                     │ allowed
                     ▼
       ┌────────────────────────────┐
       │  Delayed queue enqueue     │
       │  not_before = fulfilled_at │
       │              + 5 days      │
       └─────────────┬──────────────┘
                     │ ... time passes ...
                     ▼
       ┌────────────────────────────┐
       │  Policy gate (fire-time)   │
       │  ├ re-check opt-out        │
       │  ├ Shopify GET order       │
       │  ├ financial_status check  │ ── refunded ─► log + drop
       │  └ select_review_platform  │
       └─────────────┬──────────────┘
                     │ proceed
                     ▼
       ┌────────────────────────────┐
       │  POST /v4/review-invites   │
       │  on 200:                   │
       │   ├ outbox.record_sent     │
       │   └ cooldown.mark_sent     │
       └─────────────┬──────────────┘
                     │
                     ▼  (async, hours later)
       ┌────────────────────────────┐
       │  Webhook: invitation.*     │
       │  ├ delivered → outbox=del  │
       │  └ failed    → outbox=fail │
       │                ├ rollback  │
       │                │  cooldown │
       │                └ flag opt  │
       │                   if STOP  │
       └────────────────────────────┘

       ┌────────────────────────────┐
       │  Webhook: review.received  │
       │  ├ verify signature        │
       │  ├ idempotency.claim(id)   │
       │  ├ classify(rating)        │
       │  │   ≤2 → escalate         │
       │  │   ≥4 → thank            │
       │  │    3 → log              │
       │  └ return 200              │
       └────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their incident before reading a line of code, then walks through one mitigation per failure mode in fixed order.
- **PRD.md** is the product framing for stakeholders who need to justify the work (personas, acceptance criteria, success metrics).
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together.
- **references/errors.md** is a flat `ERR_REVIEW_*` lookup table that on-call references under stress.
- **references/examples.md** is a cookbook of complete worked snippets — no truncated `...` placeholders.
- **references/implementation.md** is the portability layer: SQLite cooldown backend, queue backend options, sentiment classifier alternatives, Node.js port.
- **scripts/** are executable operator tools; each prints structured output (JSON on stdout, human on stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read              # config, contact records, outbox snapshots for audits
  - Write             # write audit reports, replay outputs, runbook docs
  - Edit              # patch config for cooldown/buffer tuning
  - Bash(curl:*)      # call Podium and Shopify endpoints in worked examples
  - Bash(jq:*)        # parse webhook payloads in shell examples
  - Bash(python3:*)   # run the bridge service and CLIs
  - Bash(redis-cli:*) # inspect cooldown keys + outbox hashes during incidents
  - Grep              # search logs for skipped/sent events during forensic work
```

`Bash(rm:*)`, `Bash(git:*)`, and any network tool other than `curl` are intentionally absent — this skill never deletes files, never makes git commits, and never reaches non-Podium / non-Shopify endpoints directly.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-review-request-automation/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml             # cooldown window, refund buffer, platform fallback rules
├── references/
│   ├── errors.md                 # ERR_REVIEW_001..014 with cause + solution
│   ├── examples.md               # 10 worked examples
│   └── implementation.md         # SQLite backend, queue options, Node port, sentiment classifier
└── scripts/
    ├── shopify_to_podium_bridge.py    # webhook listener + policy gate + scheduler
    ├── cooldown_check.py              # CLI: query cooldown state for a phone
    ├── review_response_handler.py     # CLI: replay-process a stored review.received event
    └── optout_compliance_audit.py     # CLI: cross-flow opt-out drift detection
```

## API Integration Architecture

The review-request surface spans two upstream APIs (Podium, Shopify) and seven distinct event types. Each is wrapped by exactly one handler:

| Endpoint / Event | Direction | Wrapping |
|---|---|---|
| `POST /v4/review-invitations` (Podium) | outbound | `send_review_request()` — one call site; all sends flow through here |
| `GET /admin/api/2024-04/orders/{id}` (Shopify) | outbound | `shopify.get_order()` — used at fire-time for refund re-check |
| `GET /v4/contacts/{id}` (Podium) | outbound | `contacts.get_by_phone()` — opt-out source-of-truth read |
| `PATCH /v4/contacts/{id}` (Podium) | outbound | `contacts.set_keyword_optout()` — STOP-reply propagation |
| `orders/fulfilled` (Shopify webhook) | inbound | `shopify_fulfilled_handler()` |
| `review_invitation.delivered` (Podium webhook) | inbound | `outbox.record_delivered()` |
| `review_invitation.failed` (Podium webhook) | inbound | `outbox.record_failed()` |
| `review.received` (Podium webhook) | inbound | `handle_review_received()` |

All outbound calls share a single `httpx.AsyncClient` factory with `timeout=10` and connection pooling. The Podium-side authentication is handled by `podium-auth` — this skill never refreshes a token directly.

## Data Flow Architecture

```
[Shopify]                  [Bridge]                 [Redis]           [Podium]
    │                         │                        │                  │
    │ orders/fulfilled        │                        │                  │
    ├────────────────────────►│                        │                  │
    │                         │ is_opted_out, can_send │                  │
    │                         ├───────────────────────►│                  │
    │                         │                        │                  │
    │                         │ enqueue not_before+5d  │                  │
    │                         ├───────────────────────►│                  │
    │                         │                        │                  │
    │ (5 days later)          │                        │                  │
    │                         │◄───────────────────────┤ ready to fire    │
    │ GET order               │                        │                  │
    │◄────────────────────────┤                        │                  │
    │ financial_status: paid  │                        │                  │
    ├────────────────────────►│                        │                  │
    │                         │ POST review-invitations│                  │
    │                         ├───────────────────────────────────────────►│
    │                         │ 200 + invitation_id    │                  │
    │                         │◄───────────────────────────────────────────┤
    │                         │ outbox.record_sent,    │                  │
    │                         │ cooldown.mark_sent     │                  │
    │                         ├───────────────────────►│                  │
    │                         │                        │                  │
    │                         │ (hours later)          │                  │
    │                         │ webhook invitation.del │                  │
    │                         │◄───────────────────────────────────────────┤
    │                         │ outbox.record_delivered│                  │
    │                         ├───────────────────────►│                  │
```

The cooldown write happens only on Podium-200, not at schedule-time. This is the contract that makes failed-send rollback correct.

## Error Handling Strategy

Three error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PodiumDeliveryError` (transient) | 5xx from `/v4/review-invitations`, network timeout | Re-enqueue with exponential backoff (max 4 attempts) |
| `PodiumDeliveryError` (permanent) | 400 invalid_phone, 409 cooldown_violation | Log + skip; never retry |
| `ReviewWebhookError` | signature mismatch, malformed payload | Return non-2xx for signature mismatch (deters bad actors); return 200 + log for malformed (Podium retries would loop) |

The retry policy is in `with_retry()` in the library. Permanent errors short-circuit retry. The webhook handlers always return 200 once signature verification passes and idempotency claim succeeds — application errors are logged but never bubble to Podium as a retry signal.

## Composability & Stacking

`podium-review-request-automation` is a **policy layer** that depends on three foundational skills and references one peer skill for opt-out merge semantics:

```
                  podium-review-request-automation   ◄── this skill
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   podium-auth         podium-rate-          podium-webhook-
        │              limit-survival          reliability
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                  podium-contact-dedup   (referenced for opt-out merge)
```

A consumer building on this skill gets:

- Token refresh + scope validation + decay monitoring (from `podium-auth`)
- Per-campaign rate-limit handling with `Retry-After` (from `podium-rate-limit-survival`)
- Durable inbound webhook persistence with signature verification (from `podium-webhook-reliability`)
- Merged opt-out source-of-truth across SMS, email, and review flows (from `podium-contact-dedup`)

The policy gate in this skill is the convergence point of all four upstream layers.

## Performance & Scalability

- **Single-merchant throughput**: bounded by Podium's per-campaign rate limit, not by this skill. The bridge is stateless; horizontal scaling is unrestricted.
- **Cooldown lookup latency**: single Redis GET per send decision — sub-millisecond.
- **Delayed queue cost**: O(1) per scheduled send; O(N) memory in queued depth. With Redis streams, 1M deferred sends is ~200 MB RSS.
- **Outbox memory**: O(invitations × 7 days TTL). A merchant sending 10K/day = 70K records — trivial.
- **Webhook handler concurrency**: bounded by Podium's webhook fanout (typically ≤10 concurrent per merchant). Idempotency claim is the only contention point.

## Security & Compliance

- **Webhook signature verification**: HMAC-SHA256 on every inbound webhook before any side effect. Secret rotation handled by `podium-auth`'s rotation runbook.
- **Phone number handling**: every phone normalized to E.164 before keying any state; raw phone strings never logged.
- **PII in logs**: order IDs and `invitation_id`s are logged; phone numbers, customer names, and review text are redacted at log emission.
- **Opt-out source-of-truth**: a single contact record is authoritative; per-flow opt-out flags are denormalized read-replicas but writes always flow through the source.
- **Audit trail**: every send/skip decision emits a structured event (`review_send_succeeded`, `review_send_skipped_cooldown`, `review_send_skipped_optout`, `review_send_skipped_refund`) with `order_id` and a redacted phone hash. The audit-query CLI joins these against the outbox.
- **TCPA / Spam Act posture**: defaulted-conservative — when in doubt the system does not send. Operators may relax (shorten cooldown, drop the buffer, etc.) but the default config passes a reasonable jurisdiction-agnostic compliance bar.

## Testing Strategy

- **Unit tests**: mock Podium + Shopify clients; verify gate decisions for cooldown-hit, opt-out-hit, refund-status, multi-platform fallback, and signature mismatch.
- **Integration tests**: against a Podium sandbox campaign and a Shopify dev store; verify a full schedule → fire → outbox-reconcile cycle.
- **Chaos test**: SIGKILL the bridge between Podium 200 and `cooldown.mark_sent` — verify the next webhook (`invitation.failed` or `invitation.delivered`) still resolves the outbox and no duplicate send fires.
- **Soak test**: 7-day continuous run with 10K simulated orders, 3% refund rate, 12% carrier-failure rate — verify zero in-cooldown sends, zero refunded-order sends, ≥95% carrier-failure detection within 24h.
- **Compliance test**: bulk-load a CSV of opted-out phones into the merged contact record; verify the bridge skips 100% of those phones at both schedule-time and fire-time, then verify the audit CLI detects drift when one flow is manually mutated out of sync.
- **Webhook replay test**: replay the same `review.received` event 50 times within the idempotency TTL; verify exactly one Slack escalation fires.
