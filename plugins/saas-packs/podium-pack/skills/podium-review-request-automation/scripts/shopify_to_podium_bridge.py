#!/usr/bin/env python3
"""shopify_to_podium_bridge.py — local Shopify → Podium webhook bridge for dev / staging.

Listens on the configured port and exposes:
  POST /shopify/orders-fulfilled       — schedule-time gate, enqueue deferred send
  POST /podium/review-received         — sentiment classification, route negative reviews
  POST /podium/invitation-delivered    — outbox resolution (delivered)
  POST /podium/invitation-failed       — outbox resolution + cooldown rollback
  GET  /healthz                        — liveness
  GET  /metrics                        — audit-event counters (text/plain Prometheus exposition)

Usage:
  shopify_to_podium_bridge.py \\
    --port 8787 \\
    --shopify-webhook-secret-env SHOPIFY_WEBHOOK_SECRET \\
    --podium-webhook-secret-env PODIUM_WEBHOOK_SECRET \\
    --podium-campaign-id "{your-podium-campaign-id}" \\
    --redis-url "$REDIS_URL" \\
    --cooldown-days 30 \\
    --refund-buffer-days 5

This script is illustrative — it implements the policy gate and the durable enqueue,
but does NOT include the deferred-send worker loop (a separate process, not shown).
Run with `--print-config-only` to dump the resolved configuration without binding the port.
"""

from __future__ import annotations
import argparse
import base64
import hmac
import hashlib
import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COUNTERS: dict[str, int] = {}
CONFIG: dict = {}


def incr(name: str) -> None:
    COUNTERS[name] = COUNTERS.get(name, 0) + 1


def verify_shopify_hmac(body: bytes, header: str, secret: str) -> bool:
    digest = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(digest, header or "")


def verify_podium_sig(body: bytes, header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")


def normalize_e164(raw: str) -> str | None:
    # Lightweight normalization. Production deployments should use the `phonenumbers`
    # library — see references/implementation.md.
    if not raw:
        return None
    cleaned = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if cleaned.startswith("+") and cleaned[1:].isdigit() and 8 <= len(cleaned) - 1 <= 15:
        return cleaned
    return None


def redis_client():
    import redis as redis_lib

    return redis_lib.from_url(CONFIG["redis_url"], decode_responses=True)


def can_send(phone: str) -> tuple[bool, float]:
    r = redis_client()
    last = r.get(f"podium:cooldown:{phone}")
    if last is None:
        return True, 0.0
    elapsed = time.time() - float(last)
    cooldown_seconds = CONFIG["cooldown_days"] * 86400
    if elapsed >= cooldown_seconds:
        return True, 0.0
    return False, (cooldown_seconds - elapsed) / 86400


def is_opted_out(phone: str) -> bool:
    # Stub for the dev bridge — production deployments query the merged-contacts service.
    # Returning False here means the dev bridge defaults to "not opted out" unless the
    # operator pre-loads opt-out records into Redis under the canonical key.
    r = redis_client()
    raw = r.hgetall(f"podium:contact:{phone}")
    if not raw:
        return False
    flags = ["marketing_sms_opt_out", "review_request_opt_out", "global_unsubscribe", "podium_keyword_optout"]
    return any(raw.get(f) == "true" for f in flags)


def enqueue_deferred(payload: dict, not_before: float) -> str:
    r = redis_client()
    msg_id = str(uuid.uuid4())
    pipe = r.pipeline()
    pipe.zadd(CONFIG["queue_zkey"], {msg_id: not_before})
    pipe.hset(CONFIG["queue_hkey"], msg_id, json.dumps(payload))
    pipe.execute()
    return msg_id


def handle_orders_fulfilled(body: bytes, headers: dict) -> tuple[int, str]:
    secret = os.environ.get(CONFIG["shopify_secret_env"], "")
    if not verify_shopify_hmac(body, headers.get("X-Shopify-Hmac-Sha256", ""), secret):
        incr("webhook_signature_mismatch_shopify")
        return 401, "bad hmac"

    try:
        order = json.loads(body)
        phone = normalize_e164(order.get("customer", {}).get("phone", ""))
    except (json.JSONDecodeError, AttributeError):
        incr("shopify_malformed")
        return 200, "malformed"

    if not phone:
        incr("review_send_skipped_phone_invalid")
        return 200, "skipped:phone_invalid"

    if is_opted_out(phone):
        incr("review_send_skipped_optout")
        return 200, "skipped:optout"

    allowed, _ = can_send(phone)
    if not allowed:
        incr("review_send_skipped_cooldown")
        return 200, "skipped:cooldown"

    send_after = time.time() + CONFIG["refund_buffer_days"] * 86400
    enqueue_deferred(
        {"order_id": order["id"], "phone": phone, "campaign_id": CONFIG["campaign_id"]},
        send_after,
    )
    incr("review_send_scheduled")
    return 200, "scheduled"


def handle_review_received(body: bytes, headers: dict) -> tuple[int, str]:
    secret = os.environ.get(CONFIG["podium_secret_env"], "")
    if not verify_podium_sig(body, headers.get("X-Podium-Signature", ""), secret):
        incr("webhook_signature_mismatch_podium")
        return 401, "bad sig"
    try:
        event = json.loads(body)
        rating = int(event["data"]["rating"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return 200, "malformed"

    # Idempotency claim
    r = redis_client()
    if not r.set(f"podium:idemp:review:{event['id']}", "1", nx=True, ex=86400):
        incr("review_received_duplicate")
        return 200, "duplicate"

    if rating <= 2:
        incr("review_received_negative")
        # Production deployment fires Slack here. Dev bridge logs only.
    elif rating >= 4:
        incr("review_received_positive")
    else:
        incr("review_received_neutral")
    return 200, "ok"


def handle_invitation_delivered(body: bytes, headers: dict) -> tuple[int, str]:
    secret = os.environ.get(CONFIG["podium_secret_env"], "")
    if not verify_podium_sig(body, headers.get("X-Podium-Signature", ""), secret):
        return 401, "bad sig"
    try:
        event = json.loads(body)
        invitation_id = event["data"]["invitation_id"]
    except (json.JSONDecodeError, KeyError):
        return 200, "malformed"
    r = redis_client()
    r.hset(f"podium:outbox:{invitation_id}", "status", "delivered")
    r.hset(f"podium:outbox:{invitation_id}", "delivered_at", time.time())
    incr("invitation_delivered")
    return 200, "ok"


def handle_invitation_failed(body: bytes, headers: dict) -> tuple[int, str]:
    secret = os.environ.get(CONFIG["podium_secret_env"], "")
    if not verify_podium_sig(body, headers.get("X-Podium-Signature", ""), secret):
        return 401, "bad sig"
    try:
        event = json.loads(body)
        invitation_id = event["data"]["invitation_id"]
        reason = event["data"].get("failure_reason", "unknown")
    except (json.JSONDecodeError, KeyError):
        return 200, "malformed"
    r = redis_client()
    phone = r.hget(f"podium:outbox:{invitation_id}", "phone")
    r.hset(f"podium:outbox:{invitation_id}", "status", "failed")
    r.hset(f"podium:outbox:{invitation_id}", "failure_reason", reason)
    # Cooldown rollback — the customer never received the message
    if phone:
        r.delete(f"podium:cooldown:{phone}")
    incr("invitation_failed")
    incr(f"invitation_failed_{reason}")
    return 200, "ok"


class Handler(BaseHTTPRequestHandler):
    routes = {
        "/shopify/orders-fulfilled": handle_orders_fulfilled,
        "/podium/review-received": handle_review_received,
        "/podium/invitation-delivered": handle_invitation_delivered,
        "/podium/invitation-failed": handle_invitation_failed,
    }

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "path": self.path,
                    "msg": fmt % args,
                }
            )
            + "\n"
        )

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            for name, value in sorted(COUNTERS.items()):
                self.wfile.write(f"podium_bridge_{name} {value}\n".encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        handler = self.routes.get(self.path)
        if not handler:
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        headers = {k: v for k, v in self.headers.items()}
        try:
            status, msg = handler(body, headers)
        except Exception as e:
            sys.stderr.write(json.dumps({"error": str(e), "path": self.path}) + "\n")
            status, msg = 500, "internal error"
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode() + b"\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--shopify-webhook-secret-env", default="SHOPIFY_WEBHOOK_SECRET")
    ap.add_argument("--podium-webhook-secret-env", default="PODIUM_WEBHOOK_SECRET")
    ap.add_argument(
        "--podium-campaign-id", required=True, help="Podium campaign ID — pass {your-podium-campaign-id} for redaction"
    )
    ap.add_argument("--redis-url", required=True)
    ap.add_argument("--cooldown-days", type=int, default=30)
    ap.add_argument("--refund-buffer-days", type=int, default=5)
    ap.add_argument("--queue-name", default="podium-review-deferred")
    ap.add_argument("--print-config-only", action="store_true")
    args = ap.parse_args()

    CONFIG.update(
        {
            "shopify_secret_env": args.shopify_webhook_secret_env,
            "podium_secret_env": args.podium_webhook_secret_env,
            "campaign_id": args.podium_campaign_id,
            "redis_url": args.redis_url,
            "cooldown_days": args.cooldown_days,
            "refund_buffer_days": args.refund_buffer_days,
            "queue_zkey": f"queue:{args.queue_name}:scheduled",
            "queue_hkey": f"queue:{args.queue_name}:payloads",
        }
    )

    if args.print_config_only:
        print(json.dumps({k: v for k, v in CONFIG.items() if k != "redis_url"}, indent=2))
        return 0

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    sys.stderr.write(f"bridge listening on :{args.port}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("shutdown\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
