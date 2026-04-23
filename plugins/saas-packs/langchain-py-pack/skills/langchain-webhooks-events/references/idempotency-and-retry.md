# Idempotency and Retry — Keys, Signing, Receiver De-dup

At-least-once transports mean receivers see duplicates. Without idempotency,
duplicates get processed twice — double-charged analytics, double-triggered
downstream jobs, double-sent notifications. This reference defines the key
scheme, HMAC signing, retry budget, and receiver-side de-dup.

## Idempotency key scheme

```
idempotency_key = f"{run_id}:{event_type}:{step_index}"
```

| Component | Source | Purpose |
|---|---|---|
| `run_id` | `str(uuid.uuid4())` generated at handler init | Uniquely identifies the chain invocation; propagates into subgraphs |
| `event_type` | `tool_end` / `chain_end` / `llm_end` / `tool_error` | Distinguishes events of different types within the same run |
| `step_index` | Monotonic counter inside the handler instance | Unique ordinal within `(run_id, event_type)` |

Properties:

- **Deterministic for retries.** Re-dispatching the exact same event from the
  same `_safe_send` call produces the exact same key — receiver dedupes.
- **Unique across legitimate re-invocations.** If the same tool fires twice in
  a chain, `step_index` differs — both events reach the receiver.
- **Run-scoped.** A fresh invocation of the same chain gets a new `run_id` —
  no collision with prior runs.

**Anti-pattern:** using the LangChain `run_id` kwarg directly. Tools that are
called multiple times in one run fire `on_tool_end` with different `run_id`
values — which is fine — but if you aggregate them into a single event or
collapse them, the receiver dedupes legitimate work away.

## HMAC-SHA256 signing

Sender:

```python
import hashlib, hmac, json

body = json.dumps({"event": event_type, "data": payload}, sort_keys=True).encode()
sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
headers["X-Signature-256"] = f"sha256={sig}"
```

`sort_keys=True` is non-negotiable — without it, Python dict ordering changes
the bytes you sign, and the receiver's independent re-serialization won't
match.

Receiver (FastAPI example):

```python
from fastapi import FastAPI, Request, HTTPException, Header

@app.post("/webhooks/langchain")
async def receive(
    request: Request,
    x_signature_256: str = Header(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    body = await request.body()
    expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")

    # De-dup — see below
    if not await mark_seen(idempotency_key, ttl=86400):
        return {"status": "duplicate"}

    await process(json.loads(body))
    return {"status": "ok"}
```

`hmac.compare_digest` is timing-safe — do not use `==` for signature comparison
(timing attacks can leak the signature byte-by-byte).

## Retry budget: 1s / 5s / 30s

Sender-side retry schedule:

| Attempt | Delay before | Cumulative wall clock |
|---|---|---|
| 1 (initial) | 0s | 0s |
| 2 | 1s | 1s |
| 3 | 5s | 6s |
| 4 | 30s | 36s |
| DLQ | — | 36s total |

Rationale:

- **1s**: absorbs most transient network blips (TCP re-establish, DNS TTL flip)
- **5s**: absorbs brief provider-side 503s and autoscaler cold-boots
- **30s**: absorbs longer incidents; beyond this, retry is futile in the
  critical path — the event is stale
- **DLQ at 36s**: bounded total latency. Anything longer belongs in async
  replay, not the hot path

Retry only on:

| Status / error | Retry? | Reason |
|---|---|---|
| 200-299 | No | Success |
| 400-403, 405-428, 430-499 | **No** — DLQ immediately | Client error; retry won't help |
| 404 | No — DLQ | Receiver doesn't know the endpoint; config issue |
| 408 (timeout) | Yes | Transient |
| 429 (rate limit) | Yes — honor `Retry-After` if present | Back off |
| 500-599 | Yes | Transient server error |
| Connection/timeout/DNS | Yes | Network |

## At-least-once vs at-most-once

| Model | Guarantee | Cost |
|---|---|---|
| **At-least-once** | Every event reaches receiver ≥ 1 time | Receiver must dedupe |
| **At-most-once** | Every event reaches receiver ≤ 1 time | Tolerable loss; simpler receiver |
| **Exactly-once** | Every event reaches receiver = 1 time | Requires transactional sink + dedup store; rare in practice |

Pick:

- **At-least-once**: HTTP webhooks, Kafka, Redis Streams. Default.
- **At-most-once**: SNS fan-out where loss < duplicate cost (e.g., rough-cut
  UI counters). Skip retry, skip DLQ.
- **Exactly-once approximation**: at-least-once + receiver idempotency with
  a de-dup store. Good enough for 99.9% of cases.

## Receiver de-dup with Redis SETNX

```python
from redis.asyncio import Redis

async def mark_seen(redis: Redis, key: str, *, ttl: int = 86400) -> bool:
    """Returns True if the key was NEW (process this event),
    False if DUPLICATE (skip)."""
    # SET key val EX ttl NX — atomic set-if-not-exists with expiry
    return await redis.set(f"idemp:{key}", "1", ex=ttl, nx=True) is True
```

TTL sizing:

| Event cadence | Safe TTL | Why |
|---|---|---|
| Sub-minute (per-tool-end) | 24h | Retry budget (36s) << TTL; plenty of margin |
| Sub-hour (per-run-end) | 7d | Covers long outages |
| Daily (summary events) | 30d | Covers weekly sender outages |

Do not set TTL shorter than 2x your retry budget — a delayed retry after DLQ
replay could arrive after the de-dup entry expires, causing a false-new.

## Replay from DLQ

DLQ entries are not junk — they are events worth eventually delivering. Pattern:

1. Operator verifies the receiver is healthy again
2. Run a one-shot `replay_dlq.py` script that reads the DLQ and re-sends with
   the original `idempotency_key`
3. Receiver dedupes any that already landed during normal retry
4. DLQ entry marked as replayed (move to `replayed/` prefix in S3, XDEL from
   Redis Stream)

Never re-use a fresh idempotency key on replay — you lose the dedup guarantee.

## Sender-side circuit breaker

If the DLQ is filling faster than 10 events/sec sustained for 60s, trip a
circuit breaker: stop dispatching to that sink for 5 minutes, route directly
to DLQ. Prevents a dying receiver from consuming all your retry budget and
slowing the chain:

```python
from circuitbreaker import circuit

class CBWebhookSink(WebhookSink):
    @circuit(failure_threshold=10, recovery_timeout=300, name="webhook")
    async def _send_primary(self, **kwargs):
        return await super().send(**kwargs)

    async def send(self, **kwargs):
        try:
            return await self._send_primary(**kwargs)
        except CircuitBreakerError:
            await self.dlq.send(**kwargs)
```

## Testing

Property-based test for idempotency key:

```python
from hypothesis import given, strategies as st

@given(
    run_id=st.uuids().map(str),
    event_type=st.sampled_from(["tool_end", "chain_end", "llm_end"]),
    step_index=st.integers(min_value=1, max_value=10_000),
)
def test_idempotency_key_format(run_id, event_type, step_index):
    key = f"{run_id}:{event_type}:{step_index}"
    parts = key.split(":")
    assert len(parts) == 3
    assert parts[0] == run_id
    assert parts[1] == event_type
    assert int(parts[2]) == step_index
```

Integration test for receiver de-dup:

```python
@pytest.mark.asyncio
async def test_duplicate_event_is_not_reprocessed(client, redis):
    headers = _sign({"event": "tool_end", "data": {"x": 1}}, key="k1")
    r1 = await client.post("/webhooks/langchain", headers=headers, json={...})
    r2 = await client.post("/webhooks/langchain", headers=headers, json={...})
    assert r1.json() == {"status": "ok"}
    assert r2.json() == {"status": "duplicate"}
```

## Cross-references

- [Async Callback Handler](async-callback-handler.md) — key generation in the handler
- [Dispatch Targets](dispatch-targets.md) — per-target retry behavior and DLQ
- [Subgraph Propagation](subgraph-propagation.md) — `run_id` continuity across subgraphs
