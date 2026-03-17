# PostHog Webhooks & Events -- Implementation Reference

## Overview

Implement PostHog webhook handlers with HMAC-SHA256 signature verification, action-based
event routing, and idempotent processing for analytics-driven automation.

## Prerequisites

- PostHog project with webhook subscriptions configured
- Public HTTPS endpoint (ngrok for local dev)
- Python 3.9+ or Node.js 18+

## Webhook Registration (PostHog UI)

1. Navigate to Project Settings > Webhooks
2. Add webhook URL: `https://api.example.com/posthog/webhook`
3. Select events: `action_performed`, `event`
4. Copy the secret for signature verification

## FastAPI Webhook Handler

```python
import hashlib, hmac, json, logging, os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
app = FastAPI()
WEBHOOK_SECRET = os.environ["POSTHOG_WEBHOOK_SECRET"]
_processed: set = set()


def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=") if "=" in signature else signature
    return hmac.compare_digest(expected, provided)


@app.post("/posthog/webhook")
async def handle_webhook(request: Request, x_posthog_signature: str = Header(None)):
    payload = await request.body()
    if not x_posthog_signature or not verify_signature(payload, x_posthog_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    event = json.loads(payload)
    event_id = event.get("id", "")
    if event_id and event_id in _processed:
        return JSONResponse({"status": "already_processed"})
    if event_id:
        _processed.add(event_id)
    await route_event(event)
    return JSONResponse({"status": "ok"})


async def route_event(event: dict) -> None:
    etype = event.get("event")
    distinct_id = event.get("distinct_id", "unknown")
    props = event.get("properties", {})
    logger.info("PostHog event: %s / user: %s", etype, distinct_id)
    handlers = {
        "signed_up": on_signed_up,
        "subscription_started": on_subscription_started,
        "subscription_cancelled": on_subscription_cancelled,
    }
    handler = handlers.get(etype)
    if handler:
        await handler(distinct_id, props)


async def on_signed_up(distinct_id: str, props: dict) -> None:
    email = props.get("email", distinct_id)
    plan = props.get("plan", "free")
    logger.info("New signup: %s (plan: %s)", email, plan)


async def on_subscription_started(distinct_id: str, props: dict) -> None:
    logger.info("Subscription: %s -> %s", distinct_id, props.get("plan"))


async def on_subscription_cancelled(distinct_id: str, props: dict) -> None:
    logger.warning("Cancellation: %s reason=%s", distinct_id, props.get("cancellation_reason"))
```

## Test with curl

```bash
PAYLOAD='{"id":"test-123","event":"signed_up","distinct_id":"user@example.com","properties":{"email":"user@example.com"}}'
SECRET="your-webhook-secret"
SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST http://localhost:8000/posthog/webhook \
  -H "Content-Type: application/json" \
  -H "X-PostHog-Signature: sha256=$SIG" \
  -d "$PAYLOAD"
```

## PostHog Event Types

| Event | Trigger | Key Properties |
|-------|---------|---------------|
| `$pageview` | Page load | `current_url`, `title` |
| `$identify` | User identification | `distinct_id`, user traits |
| Custom | Your app events | Defined by your code |

## Resources

- [PostHog Webhooks](https://posthog.com/docs/webhooks)
- [PostHog API](https://posthog.com/docs/api)
