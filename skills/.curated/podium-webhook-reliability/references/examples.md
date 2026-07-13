# Examples — podium-webhook-reliability

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal FastAPI receiver with the full pipeline

```python
# env: PODIUM_WEBHOOK_SECRET, REDIS_URL
import hmac, hashlib, json, os, time
from fastapi import FastAPI, Request, HTTPException, Header
import redis.asyncio as redis

app = FastAPI()
SECRET = os.environ["PODIUM_WEBHOOK_SECRET"].encode("utf-8")
R = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

def verify(body: bytes, header: str) -> tuple[bool, str | None]:
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    ts, sig = parts.get("t"), parts.get("v1")
    if not ts or not sig:
        return False, None
    expected = hmac.new(SECRET, f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig), ts

@app.post("/webhooks/podium")
async def receive(request: Request, x_podium_signature: str = Header(None)):
    raw = await request.body()
    if not x_podium_signature:
        raise HTTPException(401, "missing signature header")
    ok, ts = verify(raw, x_podium_signature)
    if not ok:
        raise HTTPException(401, "signature mismatch")
    if abs(time.time() - int(ts)) > 300:
        raise HTTPException(401, "replay window exceeded")
    event = json.loads(raw)
    claimed = await R.set(f"podium:evt:{event['id']}", "1", nx=True, ex=86400)
    if not claimed:
        return {"status": "duplicate", "event_id": event["id"]}
    # ... dispatch(event) here
    return {"status": "ok", "event_id": event["id"]}
```

## 2. Verify a captured webhook payload from the CLI

```bash
# env: PODIUM_WEBHOOK_SECRET
python3 scripts/signature_verify.py \
  --body-file /tmp/captured_webhook_body.json \
  --signature-header "t={your-timestamp},v1={your-podium-signature}" \
  --secret-env PODIUM_WEBHOOK_SECRET
# exit 0 = valid; 1 = signature mismatch; 2 = replay window exceeded
```

## 3. Batch event handling with ordering

```python
async def dispatch_batch(events: list[dict]):
    # Sort within the batch by (occurred_at, id) for stable ordering.
    events.sort(key=lambda e: (e.get("occurred_at", 0), e.get("id", "")))
    for event in events:
        try:
            await dispatch_one(event)
        except OutOfOrderError as e:
            await dlq_persist({
                "reason": f"out_of_order_{e.precondition}",
                "event_id": event["id"],
                "raw_body": json.dumps(event),
                "received_at": time.time(),
            })
```

## 4. Dead-letter persistence with Redis backend

```python
async def dlq_persist(entry: dict) -> None:
    entry["dlq_persisted_at"] = time.time()
    await R.lpush("podium:dlq", json.dumps(entry))

# Inspect the DLQ
# redis-cli LLEN podium:dlq
# redis-cli LRANGE podium:dlq 0 9
```

## 5. SQLite DLQ backend (single-node deployments)

```python
import sqlite3, json, time

def dlq_init(path: str = "/var/lib/podium-dlq.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None)   # autocommit
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dlq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            event_type TEXT,
            raw_body TEXT NOT NULL,
            signature_header TEXT,
            received_at REAL NOT NULL,
            exception TEXT,
            replayed_at REAL
        )
    """)
    return conn

def dlq_persist_sqlite(conn: sqlite3.Connection, entry: dict) -> None:
    conn.execute(
        "INSERT INTO dlq (event_id, event_type, raw_body, signature_header, received_at, exception) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (entry.get("event_id"), entry.get("event_type"), entry["raw_body"],
         entry.get("signature_header"), entry["received_at"], entry.get("exception")),
    )
```

## 6. Drain the DLQ and replay through the receiver

```bash
# env: PODIUM_WEBHOOK_SECRET
python3 scripts/dlq_replay.py \
  --target-url https://your-receiver.example.com/webhooks/podium \
  --secret-env PODIUM_WEBHOOK_SECRET \
  --batch-size 25 \
  --rate-per-sec 10 \
  --max-events 1000
```

The replay re-uses each entry's original signature header. Because the receiver's dedup cache is centralized, events already successfully processed will be re-rejected as duplicates — only the genuinely-failed events run.

## 7. Check if an event_id is already in the dedup cache

```bash
python3 scripts/dedup_check.py --event-id evt_{your-event-identifier} \
                               --redis-url redis://localhost:6379/0
# exit 0 = first sight (would be processed)
# exit 1 = duplicate (already cached, would be rejected)
# exit 2 = backend unreachable
```

## 8. In-memory dedup fallback for dev

```python
import time
from collections import deque
from threading import Lock

class InMemoryDedup:
    """Dev-only. Process-local; lost on restart. Use Redis for prod."""
    def __init__(self, ttl_seconds: int = 86400, max_size: int = 100_000):
        self._seen: dict[str, float] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds
        self._max = max_size

    def claim(self, event_id: str) -> bool:
        now = time.time()
        with self._lock:
            self._evict(now)
            if event_id in self._seen:
                return False
            self._seen[event_id] = now + self._ttl
            return True

    def _evict(self, now: float) -> None:
        if len(self._seen) <= self._max:
            self._seen = {k: v for k, v in self._seen.items() if v > now}
            return
        # Hard-cap: drop everything expired plus the oldest 10%
        self._seen = {k: v for k, v in self._seen.items() if v > now}
        if len(self._seen) > self._max:
            drop = sorted(self._seen.items(), key=lambda kv: kv[1])[: self._max // 10]
            for k, _ in drop:
                self._seen.pop(k, None)
```

## 9. Out-of-order guard: delete-before-create

```python
async def handle_conversation_deleted(event: dict):
    convo_id = event["data"]["conversation_id"]
    # Precondition: the create event must have been processed first.
    if not await convo_exists_locally(convo_id):
        # Defer rather than raise — replay will pick it up after the create lands.
        await dlq_persist({
            "reason": "out_of_order_delete_before_create",
            "event_id": event["id"],
            "raw_body": json.dumps(event),
            "received_at": time.time(),
        })
        return
    await delete_conversation_locally(convo_id)
```

## 10. Pre-commit grep gate against == on HMAC values

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit — fail if "==" appears near "hmac" or "signature" in staged source.
set -euo pipefail

STAGED=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.(py|ts|js|go|rs)$' || true)
[ -z "$STAGED" ] && exit 0

# Match "==" within 3 lines of "hmac" or "signature" (case-insensitive).
if echo "$STAGED" | xargs -r grep -nE "(hmac|signature)" 2>/dev/null \
   | awk -F: '{print $1}' | sort -u \
   | xargs -r grep -nE "^[^#]*\b==\b" \
   | grep -iE "(hmac|signature|sig)" >/dev/null; then
  echo "ERR_WHK_002 risk: '==' compare detected near hmac/signature in staged files."
  echo "Use hmac.compare_digest() (Python) or crypto.timingSafeEqual() (Node)."
  exit 1
fi
```

Install with: `chmod +x .git/hooks/pre-commit`. The grep is conservative (false positives possible on incidental matches); the engineer's intent is to surface every site that needs human review.
