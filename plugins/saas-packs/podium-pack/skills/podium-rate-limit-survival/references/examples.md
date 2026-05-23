# Examples — podium-rate-limit-survival

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal — wrap a single Podium call with the bucket

```python
# env: PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, PODIUM_REFRESH_TOKEN_FILE
import asyncio, os, httpx
from podium_auth import PodiumAuth                   # from podium-auth skill
from podium_rate_limit import TokenBucket

auth = PodiumAuth(
    client_id=os.environ["PODIUM_CLIENT_ID"],
    client_secret=os.environ["PODIUM_CLIENT_SECRET"],
    refresh_token=open(os.environ["PODIUM_REFRESH_TOKEN_FILE"]).read(),
)
bucket = TokenBucket(rate_per_minute=60, capacity=10)

async def get_contact(uid: str):
    await bucket.acquire()
    token = await auth.get_token()
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            f"https://api.podium.com/v4/contacts/{uid}",
            headers={"Authorization": f"Bearer {token}"},
        )
    r.raise_for_status()
    return r.json()

asyncio.run(get_contact("{your-contact-uid}"))
```

## 2. Per-endpoint bucket isolation

```python
ENDPOINT_BUCKETS = {
    "conversations": TokenBucket(rate_per_minute=20, capacity=5),
    "contacts":      TokenBucket(rate_per_minute=15, capacity=5),
    "reviews":       TokenBucket(rate_per_minute=15, capacity=10),
    "locations":     TokenBucket(rate_per_minute=5,  capacity=2),
    "webhooks":      TokenBucket(rate_per_minute=5,  capacity=2),
}

def endpoint_family(path: str) -> str:
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "v4":
        return parts[1]
    return "default"

async def isolated_call(method: str, path: str, **kwargs):
    family = endpoint_family(path)
    bucket = ENDPOINT_BUCKETS.get(family, ENDPOINT_BUCKETS["conversations"])
    await bucket.acquire()
    token = await auth.get_token()
    async with httpx.AsyncClient(timeout=10) as c:
        return await c.request(
            method, f"https://api.podium.com{path}",
            headers={"Authorization": f"Bearer {token}"}, **kwargs,
        )
```

A burst on `conversations.write` no longer starves `contacts.read`. Each family has its own queue.

## 3. `Retry-After` parser — both forms

```python
from podium_rate_limit import parse_retry_after

# Integer seconds — most common form Podium returns
assert parse_retry_after("30") == 30.0

# HTTP-date form
wait_s = parse_retry_after("Wed, 09 May 2026 17:05:00 GMT")
print(f"wait {wait_s:.1f}s")

# Malformed — falls back to safe default
assert parse_retry_after("forever") == 60.0
```

## 4. Retry wrapper with cap on `Retry-After`

```python
class PodiumRateLimitError(Exception): ...

async def podium_call_with_retry(method: str, path: str, max_attempts: int = 4, **kwargs):
    for attempt in range(1, max_attempts + 1):
        family = endpoint_family(path)
        await ENDPOINT_BUCKETS[family].acquire()
        token = await auth.get_token()
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.request(
                method, f"https://api.podium.com{path}",
                headers={"Authorization": f"Bearer {token}"}, **kwargs,
            )
        if r.status_code != 429:
            return r
        wait_s = min(parse_retry_after(r.headers.get("Retry-After", "60")), 120.0)
        await asyncio.sleep(wait_s)
    raise PodiumRateLimitError(f"429 persisted after {max_attempts} attempts on {path}")
```

## 5. Daily quota monitor wired into the call site

```python
# env: PODIUM_RATE_LIMIT_REDIS_URL
from podium_rate_limit import DailyQuotaMonitor

monitor = DailyQuotaMonitor(redis_url=os.environ["PODIUM_RATE_LIMIT_REDIS_URL"], quota=50_000)

async def metered_call(method: str, path: str, **kwargs):
    r = await podium_call_with_retry(method, path, **kwargs)
    if 200 <= r.status_code < 300:
        await monitor.increment()
        action = await monitor.check_and_alert()
        if action == "throttle":
            # Caller may choose to defer low-priority work
            log_warn("daily quota throttle engaged")
    return r
```

## 6. End-of-day burst smoother (the KombiLife 5pm case)

```python
from podium_rate_limit import BurstSmoother

smoother = BurstSmoother(
    bucket=ENDPOINT_BUCKETS["reviews"],
    target_window_seconds=120,
)

async def send_review_request(payload: dict):
    return await podium_call_with_retry("POST", "/v4/reviews/invitations", json=payload)

# 80 Shopify orders ship at 5pm AEST; we have 80 review-request payloads to fire.
review_payloads = build_review_payloads_from_orders(todays_shipped_orders)
results = await smoother.submit_batch(review_payloads, send_review_request)
print(f"sent {sum(1 for r in results if r.status_code < 300)}/{len(results)} review requests")
```

The 80 requests complete over ~120s with zero 429s. The trade-off — the burst takes 2 minutes instead of 30 seconds — is invisible to customers (review-request emails arriving at 17:00 vs 17:02 carries no operational meaning).

## 7. Webhook admission control (inbound → outbound amplification)

```python
from podium_rate_limit import AdmissionController

admit = AdmissionController(
    bucket=ENDPOINT_BUCKETS["reviews"],
    daily_monitor=monitor,
)

async def handle_shopify_webhook(event: dict):
    event_type = event["topic"]                       # e.g. "shopify.order.created"
    if not await admit.admit(event_type):
        # Caller decides: non-2xx (Podium retries) or queue (Shopify, no auto-retry)
        return {"status": "deferred"}, 503
    # Proceed with the outbound fan-out
    await create_or_update_contact(event["customer"])
    await smoother.submit_batch(
        [build_review_payload(event)], send_review_request,
    )
    return {"status": "ok"}, 200
```

## 8. Operator — simulate a request trace and report projected 429 count

```bash
# Input CSV: timestamp_iso,endpoint,request_count
python3 scripts/bucket_simulator.py \
  --trace ./traces/2026-05-09-prod-replay.csv \
  --rate-per-minute 60 \
  --capacity 10 \
  --output json
```

Output:

```json
{
  "trace_requests": 4127,
  "trace_window_seconds": 3600,
  "projected_429_count": 0,
  "projected_p50_queue_wait_ms": 0,
  "projected_p99_queue_wait_ms": 1840,
  "would_exhaust_daily_quota_at_request": null
}
```

If `projected_429_count` is non-zero, the bucket size is wrong for this traffic — increase `capacity` or split into per-endpoint buckets and re-run.

## 9. Operator — check today's quota consumption

```bash
python3 scripts/quota_monitor.py \
  --redis-url "$PODIUM_RATE_LIMIT_REDIS_URL" \
  --quota 50000
```

Exit codes:

- `0` = below warn (< 70%)
- `1` = warn (70–84%)
- `2` = page (85–94%)
- `3` = throttle (>= 95%)

Use in a cron / alertmanager:

```cron
*/5 * * * *  python3 /opt/podium/quota_monitor.py --quota 50000 || alert-router --tier $?
```

## 10. Operator — parse a `Retry-After` from a real 429 response

```bash
# Capture the header from a real 429
curl -sD - -o /dev/null -X POST https://api.podium.com/v4/conversations \
  -H "Authorization: Bearer {your-token}" \
  -d '{}' | grep -i retry-after
# retry-after: 30

python3 scripts/retry_after_parse.py --header "30"
# {"wait_seconds": 30.0, "absolute_wakeup_utc": "2026-05-09T17:00:30+00:00"}

python3 scripts/retry_after_parse.py --header "Wed, 09 May 2026 17:05:00 GMT"
# {"wait_seconds": 287.4, "absolute_wakeup_utc": "2026-05-09T17:05:00+00:00"}
```

Useful during on-call: paste the `Retry-After` header from a paging alert into this script and get the absolute UTC wakeup time so you know whether to wait or escalate.
