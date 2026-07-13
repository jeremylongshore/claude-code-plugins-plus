# Implementation Reference — podium-review-request-automation

Language-portability layer plus storage-backend wiring plus the operator playbook for incident response.

## SQLite cooldown backend (single-node deployment)

For single-process or single-node deployments, SQLite is a simpler backend than Redis. Same interface, persistent on disk, atomic via the database's transaction guarantees.

```python
import sqlite3, time, threading
from typing import Optional

class SQLiteCooldownGate:
    def __init__(self, db_path: str, cooldown_days: int = 30):
        self.db_path = db_path
        self.cooldown_seconds = cooldown_days * 86400
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS cooldown (
                    phone TEXT PRIMARY KEY,
                    last_contact_at REAL NOT NULL
                )
            """)

    def _conn(self):
        c = sqlite3.connect(self.db_path, isolation_level=None, timeout=5)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    def can_send(self, phone_e164: str) -> tuple[bool, Optional[float]]:
        with self._conn() as c:
            row = c.execute(
                "SELECT last_contact_at FROM cooldown WHERE phone = ?",
                (phone_e164,),
            ).fetchone()
        if row is None:
            return True, None
        elapsed = time.time() - row[0]
        if elapsed >= self.cooldown_seconds:
            return True, None
        return False, self.cooldown_seconds - elapsed

    def mark_sent(self, phone_e164: str) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO cooldown(phone, last_contact_at) VALUES (?, ?) "
                "ON CONFLICT(phone) DO UPDATE SET last_contact_at = excluded.last_contact_at",
                (phone_e164, time.time()),
            )

    def rollback(self, phone_e164: str) -> None:
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM cooldown WHERE phone = ?", (phone_e164,))
```

WAL mode is required for concurrent reads with single-writer semantics. Without it, the bridge serializes every webhook decision behind a global write lock.

## Durable queue backend options

| Backend | Best for | Trade-off |
|---|---|---|
| **Redis Streams** | Single-region, ≤1M deferred sends | Stream length grows linearly with backlog; consume-and-trim discipline required |
| **AWS SQS (delay queues)** | Multi-AZ, AWS-native deployments | 15-min hard cap on per-message delay — for 5-day buffers, use a DLQ + relay pattern |
| **Postgres `pgmq`** | Already running Postgres for other state | Lower throughput than Redis but transactional consistency with related state |
| **Cloud Tasks (GCP)** | GCP-native deployments | 30-day max scheduling horizon — fits 5-day buffer with room |

For the 5-day refund buffer, SQS's 15-minute delay-message ceiling forces a relay pattern: enqueue with a short delay to a scheduler service that re-enqueues until `not_before` passes. Redis Streams and pgmq handle the 5-day delay natively via a sorted-set scan; this skill ships the sorted-set pattern by default.

```python
# Redis sorted-set delayed queue (simplified)
import redis, json, time, uuid

class RedisDelayedQueue:
    def __init__(self, redis_url: str, queue_name: str):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.zkey = f"queue:{queue_name}:scheduled"
        self.hkey = f"queue:{queue_name}:payloads"

    def enqueue(self, payload: dict, not_before: float) -> str:
        msg_id = str(uuid.uuid4())
        pipe = self.r.pipeline()
        pipe.zadd(self.zkey, {msg_id: not_before})
        pipe.hset(self.hkey, msg_id, json.dumps(payload))
        pipe.execute()
        return msg_id

    def claim_ready(self, limit: int = 10) -> list[tuple[str, dict]]:
        now = time.time()
        # ZRANGEBYSCORE returns msg_ids whose not_before <= now
        ready_ids = self.r.zrangebyscore(self.zkey, "-inf", now, start=0, num=limit)
        out = []
        for mid in ready_ids:
            # Atomic claim: remove from sorted set; if zrem returns 1, we own it
            if self.r.zrem(self.zkey, mid) == 1:
                payload_json = self.r.hget(self.hkey, mid)
                self.r.hdel(self.hkey, mid)
                if payload_json:
                    out.append((mid, json.loads(payload_json)))
        return out
```

## Sentiment classifier alternatives

The default classifier is `rating ≤2 → escalate, rating ≥4 → thank, rating ==3 → log`. For merchants who want more granular routing:

| Alternative | When to use |
|---|---|
| **Star-rating only (default)** | Most cases. Cheap, deterministic, audit-friendly. |
| **Star-rating + keyword scan** | When merchants notice 3-star reviews with negative text being missed. Add a regex against `review.body` for `{"refund", "broken", "never", "worst", "manager"}`. |
| **LLM sentiment classification** | When the merchant has hundreds of reviews/day and wants to extract themes (`shipping`, `product_quality`, `customer_service`). Use a small classification-only model; never use a generative model for sentiment. |

The skill ships the default. The LLM upgrade is documented but not implemented inline — it belongs in a downstream skill.

## Node.js / TypeScript port

The Python bridge translates to TypeScript with two changes: `redis.Redis` becomes `ioredis`, and the policy gate uses Promise-based concurrency rather than async/await with `asyncio.Lock`.

```typescript
import Redis from "ioredis";

interface CooldownGateOpts {
  redisUrl: string;
  cooldownDays?: number;
}

export class CooldownGate {
  private r: Redis;
  private cooldownSeconds: number;

  constructor(opts: CooldownGateOpts) {
    this.r = new Redis(opts.redisUrl);
    this.cooldownSeconds = (opts.cooldownDays ?? 30) * 86400;
  }

  private key(phone: string): string {
    return `podium:cooldown:${phone}`;
  }

  async canSend(phoneE164: string): Promise<{ allowed: boolean; secondsRemaining: number | null }> {
    const last = await this.r.get(this.key(phoneE164));
    if (last === null) return { allowed: true, secondsRemaining: null };
    const elapsed = Date.now() / 1000 - parseFloat(last);
    if (elapsed >= this.cooldownSeconds) return { allowed: true, secondsRemaining: null };
    return { allowed: false, secondsRemaining: this.cooldownSeconds - elapsed };
  }

  async markSent(phoneE164: string): Promise<void> {
    await this.r.setex(this.key(phoneE164), this.cooldownSeconds, Date.now() / 1000);
  }

  async rollback(phoneE164: string): Promise<void> {
    await this.r.del(this.key(phoneE164));
  }
}
```

## E.164 phone normalization

Every key in the cooldown store, every opt-out lookup, every outbox record uses E.164. Bad normalization is the most common bug in this layer.

```python
import phonenumbers   # `pip install phonenumbers`

def normalize_e164(raw: str, default_region: str = "AU") -> str:
    """Returns E.164 (e.g. '+61412345678') or raises ValueError."""
    if not raw:
        raise ValueError("empty phone")
    try:
        parsed = phonenumbers.parse(raw, default_region)
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"unparseable phone: {e}")
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(f"invalid phone: {raw}")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
```

The `default_region` is per-merchant — a US merchant defaults to `US`, an Australian merchant to `AU`. Shopify's customer record sometimes includes a country code and sometimes does not; the default-region fallback handles the gap.

## Operator playbook — incident response

### "A customer received two requests in a week"

1. Run `cooldown_check.py --phone "<phone>"` — confirm the cooldown record exists.
2. Query the audit log for `review_send_*` events for that phone.
3. If the cooldown record is missing: a process between API-200 and `mark_sent` died. Check the outbox for the orphan invitation and verify upstream `podium-webhook-reliability` is intact.
4. If the cooldown record was correctly present but the gate logic ran twice: check for duplicate Shopify webhook delivery — Shopify retries on non-2xx, idempotency on schedule is required.

### "A refunded order got a review request"

1. Query the audit log for the `review_send_succeeded` event with the order ID.
2. Query Shopify for the order's refund timestamps.
3. If `refund_time > send_time` — refund happened after the send. The buffer cannot catch this; document the case in the customer-success runbook.
4. If `refund_time < send_time` and `send_time > scheduled_at` — the fire-time refund-status re-check failed. Verify `shopify.get_order()` is being called correctly and the Shopify API token has read access.

### "A 1-star review didn't trigger a Slack page"

1. Query the audit log for `review_received` events matching the review timestamp.
2. If no event was logged: the webhook was never received. Check Podium's webhook delivery log for that event ID; if Podium reports delivered, the bridge's signature verification or idempotency claim rejected it — check the 401 log.
3. If the event was logged but no escalation fired: check `escalate_negative_review` delivery confirmation. The dead-letter queue should have a record.

### "Opt-out drift across flows"

1. Run `optout_compliance_audit.py --phone "<phone>"` — the output names the divergent flag.
2. Run with `--propagate` to write the union of opt-outs to every flag.
3. Investigate the source flow that diverged — typically a separate integration writing to only one flag.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_cooldown_blocks_within_window` | unit | `can_send` returns False for a phone marked in last 30d |
| `test_cooldown_allows_after_window` | unit | `can_send` returns True for a phone marked >30d ago |
| `test_cooldown_concurrent_safety` | unit | 100 concurrent `mark_sent` for one phone produces one Redis record |
| `test_refund_buffer_skips_refunded_order` | integration | Fire-time gate skips when `financial_status=refunded` |
| `test_optout_predicate_or_semantics` | unit | Any one of 4 flags = suppress |
| `test_optout_enforced_at_both_times` | integration | Opt-out set after schedule but before fire = skip at fire |
| `test_invitation_failed_rolls_back_cooldown` | integration | `failed` webhook deletes the cooldown key |
| `test_review_received_idempotent` | integration | Same event ID twice = one escalation |
| `test_platform_fallback_to_google` | unit | Facebook campaign + no `facebook_uid` → returns google |
| `test_signature_mismatch_returns_401` | unit | Bad HMAC returns 401, never processes |
| `test_e164_normalization_strict` | unit | Unparseable phone raises, never falls back |
