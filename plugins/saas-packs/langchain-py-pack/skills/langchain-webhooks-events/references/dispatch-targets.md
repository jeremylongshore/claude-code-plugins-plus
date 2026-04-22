# Dispatch Targets — HTTP / Kafka / Redis Streams / SNS

Per-transport implementation of the `Sink` protocol. Each target has different
delivery guarantees, latency, and failure modes. Pick based on who is consuming,
not on what's most familiar.

## Target matrix

| Target | Delivery guarantee | Typical latency | Ordering | Back-pressure | Failure mode |
|---|---|---|---|---|---|
| **HTTP webhook** | At-least-once (with receiver idempotency) | 50-500ms | No | None (remote) | 5xx/timeout → retry 1s/5s/30s → DLQ |
| **Kafka (aiokafka)** | At-least-once (`enable.idempotence=true`) | 5-20ms intra-region | Per-partition | Broker-driven (acks=all) | Broker unavailable → local buffer + retry |
| **Redis Streams** | At-least-once (consumer groups + ACK) | 1-5ms intra-region | FIFO per stream | Stream length cap | Redis down → retry or spill |
| **SNS** | **At-most-once** (best-effort) | 10-100ms | No | None | Delivery loss tolerated; front with SQS FIFO for exactly-once |

Rule: customer-facing integrations get webhooks; internal telemetry gets Kafka
or Redis Streams; SNS is fan-out only when occasional loss is acceptable.

## HTTP webhook sink

The reference implementation from SKILL.md Step 3, expanded with DLQ and
pluggable retry schedule:

```python
import asyncio, hashlib, hmac, json, logging, os
from typing import Any
import httpx

log = logging.getLogger(__name__)

class WebhookSink:
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        signing_secret: bytes,
        dlq,                               # any DLQ sink — see below
        retry_delays: tuple[int, ...] = (1, 5, 30),
        request_timeout: float = 5.0,
    ):
        self.client = client
        self.url = url
        self.secret = signing_secret
        self.dlq = dlq
        self.retry_delays = retry_delays
        self.timeout = request_timeout

    async def send(self, *, idempotency_key: str, event_type: str, payload: dict[str, Any]) -> None:
        body = json.dumps({"event": event_type, "data": payload}, sort_keys=True).encode()
        sig = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "X-Signature-256": f"sha256={sig}",
            "X-Event-Type": event_type,
        }

        attempt = 0
        for delay in (0, *self.retry_delays):
            if delay:
                await asyncio.sleep(delay)
            attempt += 1
            try:
                resp = await self.client.post(self.url, content=body, headers=headers, timeout=self.timeout)
                if 200 <= resp.status_code < 300:
                    return
                # 4xx (non-429) is not retryable — payload is wrong
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    log.warning("webhook %s rejected: %s", idempotency_key, resp.status_code)
                    break
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                log.info("webhook %s attempt %d failed: %s", idempotency_key, attempt, exc)

        await self.dlq.send(idempotency_key=idempotency_key, event_type=event_type, payload=payload)
```

Client-side: share a single `httpx.AsyncClient` across the whole process
(connection pool reuse is critical at high RPS). Set `limits=httpx.Limits(max_keepalive_connections=100, max_connections=200)`.

## Kafka sink (aiokafka)

```python
import json
from aiokafka import AIOKafkaProducer

class KafkaSink:
    def __init__(self, producer: AIOKafkaProducer, topic: str):
        self.producer = producer
        self.topic = topic

    async def send(self, *, idempotency_key, event_type, payload):
        value = json.dumps({"event": event_type, "data": payload}, sort_keys=True).encode()
        # Partition key on run_id so events from the same run land on one partition → ordered
        run_id = idempotency_key.split(":", 1)[0].encode()
        await self.producer.send_and_wait(
            self.topic,
            value=value,
            key=run_id,
            headers=[("idempotency-key", idempotency_key.encode()),
                     ("event-type", event_type.encode())],
        )
```

Producer config for idempotent at-least-once:

```python
producer = AIOKafkaProducer(
    bootstrap_servers="kafka:9092",
    enable_idempotence=True,   # producer-side dedup within a session
    acks="all",                # wait for all in-sync replicas
    max_in_flight_requests_per_connection=5,  # required for idempotence
    compression_type="lz4",
)
```

On broker unavailability, `send_and_wait` raises. Catch and route to DLQ, or
buffer locally (bounded deque) and retry in a background task.

## Redis Streams sink

```python
import json
from redis.asyncio import Redis

class RedisStreamSink:
    def __init__(self, redis: Redis, stream: str, maxlen: int = 100_000):
        self.redis = redis
        self.stream = stream
        self.maxlen = maxlen

    async def send(self, *, idempotency_key, event_type, payload):
        await self.redis.xadd(
            self.stream,
            {
                "idempotency_key": idempotency_key,
                "event_type": event_type,
                "payload": json.dumps(payload),
            },
            maxlen=self.maxlen,
            approximate=True,   # ~10% faster, bounded memory
        )
```

Consumers use `XREADGROUP` + `XACK` for at-least-once delivery. If a consumer
crashes before `XACK`, another consumer picks up via `XPENDING`/`XCLAIM`.

## SNS sink (fan-out only)

```python
import json

class SNSSink:
    def __init__(self, sns_client, topic_arn: str):
        self.sns = sns_client
        self.topic_arn = topic_arn

    async def send(self, *, idempotency_key, event_type, payload):
        # SNS is best-effort. No DLQ on the publisher side — subscribers must
        # own their DLQ (e.g., SQS FIFO with a redrive policy).
        await self.sns.publish(
            TopicArn=self.topic_arn,
            Message=json.dumps({"event": event_type, "data": payload}),
            MessageAttributes={
                "idempotency-key": {"DataType": "String", "StringValue": idempotency_key},
                "event-type": {"DataType": "String", "StringValue": event_type},
            },
        )
```

For exactly-once-style delivery, SNS → SQS FIFO with content-based dedup on
`idempotency_key`. Do not reach for SNS if you cannot tolerate any loss.

## Composite fan-out sink

Dispatch to multiple sinks from one handler:

```python
import asyncio

class CompositeSink:
    def __init__(self, *sinks):
        self.sinks = sinks

    async def send(self, **kwargs):
        # gather with return_exceptions — one sink's failure must not block others
        results = await asyncio.gather(
            *(s.send(**kwargs) for s in self.sinks),
            return_exceptions=True,
        )
        for sink, result in zip(self.sinks, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning("sink %s failed: %s", type(sink).__name__, result)
```

`asyncio.gather(return_exceptions=True)` is the key — without it, the first
failure cancels the rest.

## Dead letter queue patterns

**Redis Stream DLQ** (simplest — co-located with primary Redis):

```python
class RedisDLQ:
    def __init__(self, redis: Redis, stream: str = "webhooks:dlq"):
        self.redis = redis
        self.stream = stream

    async def send(self, *, idempotency_key, event_type, payload):
        await self.redis.xadd(self.stream, {
            "idempotency_key": idempotency_key,
            "event_type": event_type,
            "payload": json.dumps(payload),
        })
```

**S3/GCS DLQ** (durable; replay-from-archive):

```python
# Key: YYYY/MM/DD/run_id/idempotency_key.json
key = f"{date.today():%Y/%m/%d}/{run_id}/{idempotency_key}.json"
await s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(payload).encode())
```

Alarm on DLQ depth growth (Redis: `XLEN dlq_stream`; S3: CloudWatch object-count
metric). A healthy system has DLQ growth ~0.

## Per-target tuning notes

- **HTTP**: set per-host connection limits in `httpx.Limits`. A single slow receiver
  should not starve other dispatches
- **Kafka**: prefer `send_and_wait` over fire-and-forget `send` on the producer
  inside a callback — you want to know if the broker ack'd
- **Redis Streams**: `maxlen=N approximate=True` bounds memory. For unbounded retention,
  pair with a consumer that persists to durable storage
- **SNS**: tag messages with `MessageDeduplicationId = idempotency_key` on FIFO topics
  (standard topics don't support this)

## Cross-references

- [Async Callback Handler](async-callback-handler.md) — the handler that calls these sinks
- [Idempotency and Retry](idempotency-and-retry.md) — key construction, receiver de-dup
- [Subgraph Propagation](subgraph-propagation.md) — ensuring subagent events reach these sinks
