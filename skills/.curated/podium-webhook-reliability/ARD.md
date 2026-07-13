# ARD: Podium Webhook Reliability

## Architecture Pattern

**Receiver + sidecar.** The core is a small FastAPI receiver (`webhook_server.py`) plus a Redis sidecar for dedup and DLQ plus a set of operator CLI scripts (`signature_verify.py`, `dedup_check.py`, `dlq_replay.py`). The receiver is async-first because webhook ingest is naturally I/O-bound and benefits from coroutine concurrency; the scripts are synchronous CLIs that wrap the same primitives for operator workflows.

Pattern: **Verify-then-claim-then-dispatch with fail-closed dedup and durable DLQ.** Every request flows through a fixed pipeline: signature verify → replay-window check → JSON parse → dedup claim → batch sort → safe-dispatch (try/except into DLQ).

## Workflow

```
                  ┌──────────────────────────────────┐
                  │  Podium POST /webhooks/podium    │
                  └─────────────┬────────────────────┘
                                │  raw bytes + X-Podium-Signature
                                ▼
                  ┌──────────────────────────────────┐
                  │  verify_signature(raw, header)   │
                  │  - HMAC-SHA256 over t.<raw>      │
                  │  - hmac.compare_digest()         │
                  └─────────────┬────────────────────┘
                                │  pass
                                ▼
                  ┌──────────────────────────────────┐
                  │  within_replay_window(ts, 300s)  │
                  └─────────────┬────────────────────┘
                                │  pass
                                ▼
                  ┌──────────────────────────────────┐
                  │  json.loads(raw)                 │
                  │  events = body.get("events", []) │
                  │           or [body]              │
                  └─────────────┬────────────────────┘
                                │
                                ▼
                  ┌──────────────────────────────────┐
                  │  events.sort(key=(occurred_at,   │
                  │                   event_id))     │
                  └─────────────┬────────────────────┘
                                │
                                ▼
                  ┌──────────────────────────────────┐
                  │  for event in events:            │
                  │   ┌─ claim_event(id) → SET NX EX │
                  │   ├─ if duplicate: continue       │
                  │   ├─ try: dispatch(event)         │
                  │   └─ except: dlq_persist; raise   │
                  └─────────────┬────────────────────┘
                                │
                                ▼
                          return 200 OK

           ┌──────────────────────────────────────────┐
           │  operator: dlq_replay.py drains DLQ      │
           │  ├ read entries from Redis list / SQLite │
           │  └ POST to receiver (same pipeline runs) │
           └──────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures so a reader recognizes their problem before reading a line of code, then walks through one mitigation per failure mode in a fixed order.
- **PRD.md** is the product framing for stakeholders who need to justify the work (acceptance criteria, success metrics, risk register).
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together.
- **references/errors.md** is a flat lookup table — `ERR_WHK_001` → cause + solution — that on-call references under stress.
- **references/examples.md** is a cookbook of full worked snippets (no truncated `...` placeholders).
- **references/implementation.md** is the language-portability layer: Node.js equivalents, Redis schema, DLQ backend choices, in-memory fallback semantics for dev.
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON-on-stdout, human-on-stderr) so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read               # read config, captured payloads, source for grep audits
  - Write              # write DLQ replay logs, audit reports, new config files
  - Edit               # edit .gitignore to add secret patterns
  - Bash(curl:*)       # POST replays to the receiver, smoke-test endpoints
  - Bash(jq:*)         # parse webhook payloads + DLQ entries in shell examples
  - Bash(python3:*)    # invoke the operator scripts
  - Bash(redis-cli:*)  # inspect dedup cache + DLQ list directly
  - Grep               # audit source for == compares near hmac/signature
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes DLQ entries (only `dlq_replay.py` reads + acks) and never makes git commits. The operator commits.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-webhook-reliability/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # replay window, dedup TTL, DLQ backend, batch sizing
├── references/
│   ├── errors.md              # ERR_WHK_001..012 with cause + solution
│   ├── examples.md            # 10 worked examples
│   └── implementation.md      # Node equivalents, Redis schema, DLQ backends
└── scripts/
    ├── webhook_server.py      # FastAPI receiver with the full pipeline
    ├── signature_verify.py    # CLI: verify a captured payload + signature
    ├── dedup_check.py         # CLI: check if an event_id is cached
    └── dlq_replay.py          # CLI: drain the DLQ and re-POST to a target
```

## API Integration Architecture

The Podium webhook surface is one inbound endpoint and (for the handler's own work) a small number of outbound API calls. The receiver wraps the inbound endpoint; the handler is the consumer's responsibility but the skill provides the safe-dispatch wrapper.

| Endpoint | Method | Wrapping |
|---|---|---|
| `POST /webhooks/podium` (yours) | `webhook_server.receive()` | Single call site; all events flow through here |
| Redis `SET NX EX` | `claim_event(event_id)` | One redis call per event for dedup; atomic |
| Redis `LPUSH podium:dlq` | `dlq_persist(entry)` | One redis call per failed event |
| `GET /v4/conversations/{id}` (outbound) | `convo_exists(id)` | Optional precondition probe for out-of-order guards |

All Redis calls share a single `redis.asyncio.Redis` connection pool. The outbound `convo_exists()` probe is optional — only required if your handler uses cross-batch causal guards.

## Data Flow Architecture

```
[Podium]                              [Receiver]                    [Redis]              [Handler]
   │                                       │                            │                     │
   │  POST raw bytes + signature header    │                            │                     │
   ├──────────────────────────────────────►│                            │                     │
   │                                       │  HMAC verify (compare_digest)                    │
   │                                       │  replay window check       │                     │
   │                                       │  json.loads(raw)           │                     │
   │                                       │  sort by occurred_at       │                     │
   │                                       │                            │                     │
   │                                       │  SET NX EX 86400  ◄────────┤                     │
   │                                       │  (atomic claim)            │                     │
   │                                       │                            │                     │
   │                                       │  dispatch(event)  ──────────────────────────────►│
   │                                       │                            │                     │
   │                                       │  on exception: LPUSH dlq ─►│                     │
   │                                       │                            │                     │
   │  ◄────── 200 OK / 401 / 500 ──────────┤                            │                     │
```

The atomic `SET NX EX` is the linchpin. The handler is invoked only after the claim succeeds. If the claim is for a duplicate, the response is 200 (correct) and Podium stops retrying.

## Error Handling Strategy

Five error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `WebhookSignatureError` | Bad signature, missing header | Return 401; do NOT log body |
| `WebhookReplayError` | Timestamp outside ±300s window | Return 401; do NOT log body |
| `WebhookDuplicateError` (sentinel) | Event already in dedup cache | Return 200 with `status: duplicate` |
| `WebhookDispatchError` | Handler raised | DLQ persist + return 500; Podium retries |
| `DedupBackendUnavailable` | Redis unreachable | Return 503; Podium retries (fail-closed) |

Retry policy is Podium's, not the receiver's. The receiver's job is to return the right status code and persist the right side-effect (dedup claim or DLQ entry) before responding.

## Composability & Stacking

`podium-webhook-reliability` stacks on top of `podium-auth` (the foundation layer) and is consumed by every event-driven downstream skill in the pack. The webhook receiver itself does not need OAuth tokens to verify signatures — the signing secret is separate — but every handler that the receiver dispatches into will call back into the Podium API and needs `podium-auth` for token management.

```
podium-call-transcript-pipeline       podium-webchat-handler       podium-review-request-automation
                 │                              │                                  │
                 └──────────────┬───────────────┴──────────────┬───────────────────┘
                                ▼                              ▼
                       podium-webhook-reliability  ◄── this skill (event ingest layer)
                                                              │
                                                              ▼
                                                       podium-auth   (token layer for handler callbacks)
```

A consumer skill that holds a `safe_dispatch()` wrapper gets free signature verification, replay window enforcement, dedup, DLQ, and ordered batch dispatch without re-implementing any of it. The consumer only writes the per-event-type handler bodies.

## Performance & Scalability

- **Per-request latency**: HMAC-SHA256 + replay window + JSON parse + Redis `SET NX EX` = ~5–10 ms at p95 with Redis on the same VPC. Dispatch latency is handler-dominated.
- **Single-receiver throughput**: ~2,000 req/s on a 2-core uvicorn worker before tuning; Redis is rarely the bottleneck.
- **Multi-receiver throughput**: horizontal scaling is safe — dedup is centralized in Redis, so two receivers cannot both claim the same event.
- **DLQ size**: bounded by failure rate × time to fix. At 1% failure and 100 req/s, that's ~3,600/hour. Redis lists handle this comfortably; SQLite is fine up to ~10k entries; JSONL has no practical limit (use only when nothing else works).
- **Replay throughput**: bounded by handler throughput, not receiver. Default rate is 10 req/s to avoid overwhelming the downstream handler post-incident.

## Security & Compliance

- **Signing secret at rest**: SOPS + age (Intent Solutions standard). Plaintext never lands on disk in prod.
- **Signing secret in transit**: Podium endpoints enforce TLS 1.2+; receivers must enforce the same on inbound.
- **Body logging on signature failure**: forbidden. A failed signature is an attacker probe; logging the body teaches the attacker which signatures get logged. Log only the source IP, the timestamp, and the failure class.
- **Replay window**: 300s default. Tune down to 60s if your clock infrastructure is NTP-tight; tune up to 600s if you have global edge receivers with measured skew.
- **Constant-time compare**: enforced via `hmac.compare_digest`. A pre-commit grep gate fails the build if `==` appears near `hmac` or `signature` in source.
- **DLQ contents**: include the raw body and the signature header, both of which are sensitive. Encrypt the DLQ backend at rest (Redis ACL + TLS + persistent-volume encryption; SQLite file mode 0600; JSONL on an encrypted FS).

## Testing Strategy

- **Unit tests**: signature verify happy path; signature verify with one byte mutated; missing header; replay window pass / fail (skew + and -); `compare_digest` use (verify the code path via mutation testing that `==` would fail an adversarial timing test).
- **Integration tests**: against an ephemeral Redis (`docker run redis:7`); verify atomic dedup; verify DLQ persist on raise; verify replay drains.
- **Soak test**: 24h continuous run with synthetic Podium events at 50 req/s; verify zero forged-event acceptance, zero double-dispatch, zero DLQ-without-replay-possibility.
- **Chaos test**: kill Redis mid-batch and verify the receiver returns 503 (fail-closed) rather than processing without dedup.
- **Replay correctness test**: send 1,000 events with 50 deliberately-failing; fix the handler bug; drain DLQ; verify exactly the 50 are replayed and the 950 are not re-dispatched.
- **Out-of-order test**: deliver `conversation.deleted` before `conversation.created`; verify the delete defers to DLQ with `reason: out_of_order_*` and is replayed successfully after the create lands.
