# ARD: Podium Rate Limit Survival

## Architecture Pattern

**Library + scripts.** The core of this skill is a small in-process rate-limiting library (`TokenBucket`, `DailyQuotaMonitor`, `BurstSmoother`, `AdmissionController`, `parse_retry_after`) plus four operator CLI scripts (`bucket_simulator.py`, `quota_monitor.py`, `burst_smoother.py`, `retry_after_parse.py`). The library is async-first because every realistic Podium integration is webhook-driven and benefits from coroutine concurrency; the scripts are synchronous CLIs that wrap the library for capacity planning and on-call workflows.

Pattern: **Token-bucket admission control with per-family isolation, atomic daily counter, and proactive burst smoothing.**

## Workflow

```
                     ┌──────────────────────────────────────┐
                     │  Inbound event (webhook, scheduler)  │
                     └─────────────────┬────────────────────┘
                                       │
                                       ▼
                     ┌──────────────────────────────────────┐
                     │  AdmissionController.admit(event)    │
                     │  ├ lookup amplification_factor       │
                     │  ├ compute remaining daily budget    │
                     │  └ deny if cost > 5% of remaining    │
                     └─────────────────┬────────────────────┘
                                       │ admitted
                                       ▼
                     ┌──────────────────────────────────────┐
                     │  endpoint_family(path)               │
                     │  → conversations / contacts / ...    │
                     └─────────────────┬────────────────────┘
                                       │
                                       ▼
                     ┌──────────────────────────────────────┐
                     │  TokenBucket[family].acquire()       │
                     │  ├ refill from rate_per_sec          │
                     │  ├ if tokens < 1: sleep(deficit/rate)│
                     │  └ decrement and return              │
                     └─────────────────┬────────────────────┘
                                       │
                                       ▼
                     ┌──────────────────────────────────────┐
                     │  HTTP POST /v4/<family>/...          │
                     │  ├ if 429:                           │
                     │  │   wait = parse_retry_after(hdr)   │
                     │  │   sleep min(wait, 120s)           │
                     │  │   retry (max 4 attempts)          │
                     │  └ else: return response             │
                     └─────────────────┬────────────────────┘
                                       │ success
                                       ▼
                     ┌──────────────────────────────────────┐
                     │  DailyQuotaMonitor.increment()       │
                     │  ├ INCR podium:quota:YYYY-MM-DD      │
                     │  ├ if first: EXPIRE to UTC midnight  │
                     │  └ check thresholds → warn/page/throt│
                     └──────────────────────────────────────┘

           ┌───────────────────────────────────────────────┐
           │  background: BurstSmoother (per family)       │
           │  ├ accept batch of N requests                 │
           │  ├ compute per-req delay                       │
           │  └ submit at delay through the bucket          │
           └───────────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their problem before reading code, then walks through one mitigation per failure mode in a fixed order.
- **PRD.md** is the product framing for stakeholders who need to justify the work (acceptance criteria, success metrics, risk register).
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together.
- **references/errors.md** is a flat lookup table — `ERR_RL_001` → cause + solution — that on-call references under stress.
- **references/examples.md** is a cookbook of full worked snippets (no truncated `...` placeholders).
- **references/implementation.md** is the language-portability layer: Node.js equivalents, Redis vs SQLite store wiring, and the on-call playbook for a 429 cascade in progress.
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON-on-stdout, human-on-stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read              # read config, traces, secret-store files
  - Write             # write smoothed schedules, simulator output, runbook drafts
  - Edit              # edit config to adjust bucket sizes, thresholds, allocations
  - Bash(curl:*)      # call Podium endpoints in shell examples and verify 429 behavior
  - Bash(jq:*)        # parse response headers and bodies
  - Bash(python3:*)   # invoke the operator scripts
  - Bash(redis-cli:*) # inspect daily-quota counter state directly during on-call
  - Grep              # audit call sites for unwrapped Podium calls (bypass detection)
```

`Bash(rm:*)`, `Bash(git:*)`, and `Bash(systemctl:*)` are intentionally absent — this skill never deletes files, never makes git commits, and never touches running services. On-call drafts changes; operators commit and deploy.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-rate-limit-survival/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # bucket sizes, thresholds, per-endpoint allocation, amplification map
├── references/
│   ├── errors.md              # ERR_RL_001..014 with cause + solution
│   ├── examples.md            # 10 worked examples
│   └── implementation.md      # Node.js equivalents, Redis/SQLite store wiring, 429-cascade runbook
└── scripts/
    ├── bucket_simulator.py    # CLI: replay a request trace and report projected 429 count
    ├── quota_monitor.py       # CLI: query daily-quota counter, emit warn/page/throttle
    ├── burst_smoother.py      # CLI: smooth a CSV batch over a target window
    └── retry_after_parse.py   # CLI: parse Retry-After to absolute wakeup time
```

## API Integration Architecture

The rate-limit surface touches every outbound Podium call. There is no Podium endpoint dedicated to rate limits — the architecture observes the **headers and status codes** of normal data-plane responses:

| Surface | Where observed | Wrapping |
|---|---|---|
| `429 Too Many Requests` | Any `api.podium.com/v4/*` response | `podium_call_with_retry()` parses `Retry-After`, sleeps, retries up to 4 attempts |
| `Retry-After: <seconds\|HTTP-date>` | 429 response header | `parse_retry_after()` returns seconds-to-wait, capped at 120s |
| `X-RateLimit-Remaining: <n>` (if Podium ever sends it) | Successful response header | Logged as structured field; not currently load-bearing |
| Outbound call count | Every successful call site | `DailyQuotaMonitor.increment()` after the response; non-blocking |

The token bucket and daily-quota counter are entirely client-side — Podium does not expose either. The skill instruments the client so the server's enforcement never fires in the first place.

## Data Flow Architecture

```
[Inbound webhook]                [Bucket]                  [Podium API]            [Daily counter]
       │                             │                            │                       │
       │ admit(event_type)           │                            │                       │
       ├────────────────────────────►│                            │                       │
       │  remaining = quota - count  │                            │                       │
       │  cost = AMPLIFICATION[type] │                            │                       │
       │  if cost > remaining*0.05:  │                            │                       │
       │      deny → 503 to webhook  │                            │                       │
       │                             │                            │                       │
       │ acquire(family)             │                            │                       │
       ├────────────────────────────►│                            │                       │
       │  refill; sleep if needed    │                            │                       │
       │                             │                            │                       │
       │                             │   POST /v4/<family>/...    │                       │
       │                             ├───────────────────────────►│                       │
       │                             │  ◄ 200 OK                  │                       │
       │                             │                            │                       │
       │                             │                            │  INCR daily quota     │
       │                             ├──────────────────────────────────────────────────►│
       │                             │                            │  if first today:      │
       │                             │                            │     EXPIRE to UTC 0   │
       │                             │                            │                       │
       │                             │                            │  ratio = count/quota  │
       │                             │                            │  → warn/page/throttle │
```

The daily-quota increment happens **after** the successful response — failed calls don't count against quota, which matches Podium's accounting. The increment is non-blocking on the request path; a Redis outage degrades to a SQLite fallback, never to a request failure.

## Error Handling Strategy

Three error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PodiumRateLimitError` (transient) | 429 after `max_attempts` retries | Surface to caller; caller may queue for replay |
| `PodiumQuotaExhaustedError` | Daily quota breach (95% threshold + active throttle) | Caller respects throttle; foreground work degrades gracefully |
| `PodiumAdmissionDenied` | `AdmissionController.admit()` returned `False` | Caller returns non-2xx to webhook source (Podium retries) or queues to durable store (Shopify, etc.) |

Retry policy is in `podium_call_with_retry()`. Permanent 4xx errors (400, 401, 403) short-circuit retry — there is no value in retrying a quota-exhausted endpoint that returns 400 `quota_exhausted` until UTC midnight.

## Composability & Stacking

`podium-rate-limit-survival` is the **rate-limit foundation layer**. Every other Podium skill that makes outbound API calls depends on it for hot-path throughput. Stacking pattern:

```
podium-rag-context-bridge
        │
        ▼
podium-conversation-history-export
        │
        ▼
podium-call-transcript-pipeline ◄────── podium-webhook-reliability
        │                                       │
        ▼                                       │
podium-webchat-handler                          │
        │                                       │
        ▼                                       │
podium-review-request-automation                │
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                podium-rate-limit-survival  ◄── this skill
                        │
                        ▼
                  podium-auth
```

A consumer skill that holds a `TokenBucket` and a `DailyQuotaMonitor` gets free pacing, daily-budget visibility, and 429 survival without re-implementing any of it. The pattern mirrors `podium-auth`: stack once at the foundation, every higher layer inherits.

This skill itself stacks on `podium-auth` — every call through the bucket calls `auth.get_token()` immediately before the HTTP call. The two foundation layers compose without coupling: `podium-auth` does not know the bucket exists; the bucket does not know how tokens are minted.

## Performance & Scalability

- **Single-org throughput**: bounded by the 60 req/min documented ceiling. Bucket queueing adds latency under burst (P99 ~2s during a sustained burst); P50 latency is unchanged from the un-bucketed baseline.
- **Multi-org throughput**: each org has its own bucket and daily counter (sharded by org slug in Redis key); memory cost is O(orgs) — trivial for 50+ orgs.
- **Burst smoother cost**: O(N) memory per batch, O(N) wall time scaled by `target_window`. For KombiLife's 80-request batch over 120s = 9.6 KB memory, 120s wall time.
- **Daily counter cost**: one Redis INCR per successful call (~0.1ms). Negligible.
- **Admission controller cost**: one Redis GET per inbound event (~0.1ms). Negligible.

## Security & Compliance

- **No credentials in this layer**: the rate-limit layer is pure metadata. `auth.get_token()` is called *inside* the wrapped call site, after the bucket releases — tokens flow through this skill but are not held by it.
- **Counter integrity**: Redis INCR is atomic; no double-counting under concurrent writers. SQLite fallback uses `UPDATE ... SET count = count + 1` in a transaction.
- **PII in logs**: this layer logs `path`, `family`, `status_code`, `wait_seconds`, `daily_quota_ratio`. No request bodies, no response bodies, no customer identifiers. Path may contain a `location_uid` or `contact_uid` — operators should redact at the structured-log layer if those identifiers are sensitive in their environment.
- **Audit trail**: every 429 event, every admission denial, every threshold tier crossed logs a structured JSON event. Replayable post-incident.

## Testing Strategy

- **Unit tests**: `TokenBucket.acquire()` produces correct delays under concurrent acquirers (100 goroutines × 60 req should take ~60s); `parse_retry_after()` handles all RFC 7231 forms + malformed input; `DailyQuotaMonitor` increments atomically and TTLs correctly.
- **Property tests**: for any (rate, capacity, request-trace) input, the bucket never admits more than `rate * elapsed + capacity` requests in any window.
- **Integration tests**: against a stubbed Podium endpoint that 429s on a configurable schedule; verify the retry wrapper honors `Retry-After`.
- **Soak test**: 24-hour continuous burst at 80% of the documented ceiling; verify zero data loss, daily counter ends at exactly the call count, TTL fires at UTC midnight.
- **Chaos test**: kill the Redis instance mid-burst; verify the SQLite fallback engages and the integration continues without failure.
- **Burst test**: replay the KombiLife 5pm AEST trace (80 requests in 30s) through the burst smoother; verify zero 429s and 120s end-to-end completion.
