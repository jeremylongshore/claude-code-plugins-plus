# Examples — podium-review-request-automation

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Shopify webhook → policy gate → schedule (Python, async)

```python
# env: REDIS_URL, PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, SHOPIFY_WEBHOOK_SECRET
import os, json, time, hmac, hashlib, base64
from policy import CooldownGate, is_opted_out, normalize_e164
from queue_lib import delayed_queue

def verify_shopify_hmac(body: bytes, header: str) -> bool:
    secret = os.environ["SHOPIFY_WEBHOOK_SECRET"].encode()
    digest = base64.b64encode(hmac.new(secret, body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(digest, header)

cooldown = CooldownGate(redis_url=os.environ["REDIS_URL"], cooldown_days=30)
REFUND_BUFFER_DAYS = 5

async def shopify_fulfilled_handler(req):
    body = await req.body()
    if not verify_shopify_hmac(body, req.headers.get("X-Shopify-Hmac-Sha256", "")):
        return 401, "bad hmac"

    order = json.loads(body)
    phone = normalize_e164(order["customer"]["phone"])

    if await is_opted_out(phone):
        return 200, "skipped:optout"
    allowed, _ = cooldown.can_send(phone)
    if not allowed:
        return 200, "skipped:cooldown"

    send_after = time.time() + REFUND_BUFFER_DAYS * 86400
    await delayed_queue.enqueue(
        topic="podium.review.send",
        payload={"order_id": order["id"], "phone": phone},
        not_before=send_after,
    )
    return 200, "scheduled"
```

## 2. Fire-time send with refund re-check

```python
# env: PODIUM_CAMPAIGN_ID, SHOPIFY_ADMIN_API_TOKEN
import httpx
from podium_auth import PodiumAuth   # from podium-auth skill

async def fire_scheduled_send(payload: dict, auth: PodiumAuth):
    order = await shopify.get_order(payload["order_id"])

    # Refund re-check
    if order.get("financial_status") in {"refunded", "partially_refunded", "voided"}:
        return {"status": "skipped", "reason": "refunded"}
    if order.get("cancelled_at"):
        return {"status": "skipped", "reason": "cancelled"}

    # Opt-out re-check (may have changed during the 5-day buffer)
    if await is_opted_out(payload["phone"]):
        return {"status": "skipped", "reason": "optout_during_buffer"}

    token = await auth.get_token()
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            "https://api.podium.com/v4/review-invitations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": os.environ["PODIUM_CAMPAIGN_ID"],
                "contact": {"phone": payload["phone"]},
                "context": {"shopify_order_id": str(order["id"])},
            },
        )
    if r.status_code == 200:
        inv = r.json()
        outbox.record_sent(inv["id"], payload["phone"], order["id"])
        cooldown.mark_sent(payload["phone"])
        return {"status": "sent", "invitation_id": inv["id"]}
    if r.status_code in (400, 409):
        return {"status": "rejected", "code": r.status_code, "body": r.text[:200]}
    raise PodiumDeliveryError(r.status_code, r.text)
```

## 3. Cooldown CLI lookup

```bash
python3 scripts/cooldown_check.py --phone "+61412345678" --redis-url "$REDIS_URL"
```

Output:

```json
{
  "phone": "+61412345678",
  "last_contact_at": 1714752000.0,
  "cooldown_days_remaining": 23.4,
  "can_send": false
}
```

Use this when a merchant asks "why didn't customer X get a request?" The CLI returns the exact gating decision.

## 4. Inbound `review_invitation.failed` with cooldown rollback

```python
# env: PODIUM_WEBHOOK_SECRET
async def invitation_failed_handler(req):
    body = await req.body()
    if not verify_podium_signature(body, req.headers.get("X-Podium-Signature", "")):
        return 401, "bad sig"

    event = json.loads(body)
    if not await idempotency.claim(event["id"], ttl_seconds=86400):
        return 200, "duplicate"

    invitation_id = event["data"]["invitation_id"]
    reason = event["data"]["failure_reason"]
    outbox.record_failed(invitation_id, reason)   # this also rolls back cooldown

    # STOP-reply propagation
    if reason in {"recipient_optout", "stop_keyword"}:
        phone = outbox.get_phone(invitation_id)
        contact = await contacts.get_by_phone(phone)
        if contact:
            await contacts.set_keyword_optout(contact["id"], True)

    return 200, "ok"
```

## 5. Inbound `review.received` with sentiment classification

```python
async def handle_review_received(req):
    body = await req.body()
    if not verify_podium_signature(body, req.headers.get("X-Podium-Signature", "")):
        return 401, "bad sig"

    event = json.loads(body)
    if not await idempotency.claim(event["id"], ttl_seconds=86400):
        return 200, "duplicate"

    review = event["data"]
    rating = review["rating"]
    platform = review["platform"]

    if rating <= 2:
        await escalate_negative_review(review)        # Slack page with delivery confirmation
    elif rating >= 4:
        await thank_positive_reviewer(review)
    # rating == 3: log only

    log_event("review_received", rating=rating, platform=platform, review_id=review["id"])
    return 200, "ok"
```

## 6. Multi-platform routing selector

```python
def select_review_platform(customer: dict, campaign: dict) -> str:
    if customer.get("preferred_review_platform"):
        return customer["preferred_review_platform"]

    target = campaign.get("default_platform", "google")
    if target == "facebook" and not customer.get("facebook_uid"):
        log_event("platform_route_fallback", from_=target, to="google",
                  customer_id=customer["id"])
        return "google"
    if target == "instagram" and not customer.get("instagram_uid"):
        log_event("platform_route_fallback", from_=target, to="google",
                  customer_id=customer["id"])
        return "google"
    return target

# Usage at fire-time, before the Podium API call
platform = select_review_platform(customer, campaign)
# pass platform into the /v4/review-invitations call as the routing target
```

## 7. Opt-out compliance audit CLI

```bash
python3 scripts/optout_compliance_audit.py --phone "+61412345678"
```

Output:

```json
{
  "phone": "+61412345678",
  "marketing_sms_opt_out": true,
  "review_request_opt_out": false,
  "global_unsubscribe": false,
  "podium_keyword_optout": false,
  "suppressed": true,
  "drift_detected": true,
  "drift_reason": "review_request_opt_out=false despite marketing_sms_opt_out=true — propagate via podium-contact-dedup"
}
```

To fix drift in-place:

```bash
python3 scripts/optout_compliance_audit.py --phone "+61412345678" --propagate
```

## 8. Replay-process a stored `review.received` event

```bash
# When a webhook was dropped and you have the original event payload from Podium's
# delivery log, replay it through the local handler.
python3 scripts/review_response_handler.py --event-file /tmp/podium-event-abc123.json
```

The script verifies signature, claims idempotency (so a real replay later is a no-op), classifies, and routes — same code path as the live handler.

## 9. Background outbox sweeper for stale `sent` records

```python
# Run hourly. Flags invitations stuck in `sent` for >24h.
import time
SLA = 86400

async def sweep_stale_sent():
    for invitation_id in outbox.scan_by_status("sent"):
        record = outbox.get(invitation_id)
        if time.time() - record["sent_at"] > SLA:
            log_event("outbox_stale_sent", invitation_id=invitation_id,
                      age_seconds=time.time() - record["sent_at"])
            # Optional: query Podium's status API to reconcile
            status = await podium.get_invitation_status(invitation_id)
            if status in {"delivered", "failed"}:
                # The webhook was dropped — synthesize the resolution from the status read.
                if status == "delivered":
                    outbox.record_delivered(invitation_id)
                else:
                    outbox.record_failed(invitation_id, reason="reconciled_from_status_read")
```

## 10. End-to-end local bridge for development

```bash
python3 scripts/shopify_to_podium_bridge.py \
  --port 8787 \
  --shopify-webhook-secret-env SHOPIFY_WEBHOOK_SECRET \
  --podium-webhook-secret-env PODIUM_WEBHOOK_SECRET \
  --podium-campaign-id "{your-podium-campaign-id}" \
  --redis-url "$REDIS_URL" \
  --cooldown-days 30 \
  --refund-buffer-days 5 \
  --log-format json
```

Bridge exposes:

- `POST /shopify/orders-fulfilled` — Shopify webhook in
- `POST /podium/review-received` — Podium review.received in
- `POST /podium/invitation-delivered` — Podium invitation.delivered in
- `POST /podium/invitation-failed` — Podium invitation.failed in
- `GET /healthz` — liveness probe
- `GET /metrics` — Prometheus exposition (audit-event counters)

Point a Shopify dev store's webhook at `http://your-host:8787/shopify/orders-fulfilled` and a Podium sandbox campaign's webhook at the corresponding Podium endpoints to exercise the full schedule → fire → reconcile cycle.
