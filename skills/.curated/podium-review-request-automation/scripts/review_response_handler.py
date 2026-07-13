#!/usr/bin/env python3
"""review_response_handler.py — replay-process a stored Podium review.received event.

Usage:
  review_response_handler.py --event-file /tmp/podium-event-abc123.json
  review_response_handler.py --event-file - < event.json
  review_response_handler.py --event-file event.json --no-escalate --dry-run

Strategy:
  Loads the event payload (as Podium would have delivered it), optionally verifies
  signature if --signature provided, claims an idempotency key, classifies sentiment,
  and routes. Used to recover from a webhook drop where the original payload was
  retrieved from Podium's delivery log.

Exit codes:
  0  processed successfully (or correctly identified as duplicate)
  1  signature mismatch
  2  event missing required fields
  3  escalation/route failed
"""

from __future__ import annotations
import argparse
import hmac
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def claim_idempotency(redis_url: str | None, event_id: str, ttl: int = 86400) -> bool:
    if not redis_url:
        return True
    try:
        import redis as redis_lib
    except ImportError:
        print("redis not installed; skipping idempotency claim", file=sys.stderr)
        return True
    r = redis_lib.from_url(redis_url, decode_responses=True)
    key = f"podium:idemp:review:{event_id}"
    return bool(r.set(key, "1", nx=True, ex=ttl))


def classify(rating: int) -> str:
    if rating <= 2:
        return "escalate"
    if rating >= 4:
        return "thank"
    return "log_only"


def escalate(review: dict, channel_url: str) -> bool:
    payload = {
        "text": (
            f":warning: Negative review ({review['rating']}*) on "
            f"{review.get('platform', 'unknown')} — "
            f"review_id={review['id']}"
        ),
    }
    req = urllib.request.Request(
        channel_url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status < 400
    except urllib.error.URLError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--event-file", required=True, help="Path to JSON event payload, or '-' for stdin")
    ap.add_argument("--signature", help="X-Podium-Signature value (optional)")
    ap.add_argument("--secret-env", default="PODIUM_WEBHOOK_SECRET")
    ap.add_argument("--redis-url-env", default="REDIS_URL")
    ap.add_argument("--channel-url-env", default="PODIUM_NEGATIVE_REVIEW_CHANNEL")
    ap.add_argument("--no-escalate", action="store_true", help="Skip escalation channel call (for offline replay)")
    ap.add_argument("--dry-run", action="store_true", help="Classify only; do not claim idempotency or escalate")
    args = ap.parse_args()

    if args.event_file == "-":
        body_bytes = sys.stdin.buffer.read()
    else:
        with open(args.event_file, "rb") as f:
            body_bytes = f.read()

    if args.signature:
        secret = os.environ.get(args.secret_env)
        if not secret:
            print(f"missing env: {args.secret_env}", file=sys.stderr)
            return 1
        if not verify_signature(body_bytes, args.signature, secret):
            print("signature mismatch", file=sys.stderr)
            return 1

    try:
        event = json.loads(body_bytes)
        review = event["data"]
        event_id = event["id"]
        rating = int(review["rating"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"event malformed: {e}", file=sys.stderr)
        return 2

    decision = classify(rating)
    out = {
        "event_id": event_id,
        "rating": rating,
        "platform": review.get("platform"),
        "decision": decision,
        "processed_at": time.time(),
    }

    if args.dry_run:
        out["dry_run"] = True
        print(json.dumps(out, indent=2))
        return 0

    if not claim_idempotency(os.environ.get(args.redis_url_env), event_id):
        out["status"] = "duplicate"
        print(json.dumps(out, indent=2))
        return 0

    if decision == "escalate" and not args.no_escalate:
        channel_url = os.environ.get(args.channel_url_env)
        if not channel_url:
            print(f"missing env: {args.channel_url_env}", file=sys.stderr)
            return 3
        if not escalate(review, channel_url):
            print("escalation channel did not confirm receipt", file=sys.stderr)
            out["status"] = "escalation_failed"
            print(json.dumps(out, indent=2))
            return 3
        out["escalated"] = True

    out["status"] = "ok"
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
