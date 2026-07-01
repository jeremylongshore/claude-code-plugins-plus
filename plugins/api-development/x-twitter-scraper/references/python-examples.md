# Xquik Python Examples

Python equivalents of the JavaScript examples in SKILL.md.

## Contents

- [Authentication](#authentication)
- [Retry with Exponential Backoff](#retry-with-exponential-backoff)
- [Extraction Workflow](#extraction-workflow)
- [Giveaway Draw](#giveaway-draw)
- [Webhook Handler (Python Standard Library)](#webhook-handler-python-standard-library)

## Authentication

```python
import json
import urllib.error
import urllib.request

def load_secret(name: str) -> str:
    """Read from your agent or platform secret store."""
    raise RuntimeError(f"Configure {name} in your secret store.")

API_KEY = load_secret("XQUIK_API_KEY")
BASE = "https://xquik.com/api/v1"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}
```

## Retry with Exponential Backoff

```python
import time, random

def xquik_fetch(path, method="GET", json_body=None, max_retries=3):
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        retry_after = None
        body = json.dumps(json_body).encode() if json_body is not None else None
        request = urllib.request.Request(
            f"{BASE}{path}", data=body, headers=HEADERS, method=method
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            status = error.code
            payload = json.loads(error.read() or b"{}")
            retry_after = error.headers.get("Retry-After")

        retryable = status == 429 or status >= 500
        if not retryable or attempt == max_retries:
            raise Exception(f"Xquik API {status}: {payload.get('error', 'request failed')}")

        delay = int(retry_after) if retry_after else base_delay * (2 ** attempt) + random.uniform(0, 1)
        time.sleep(delay)
```

## Extraction Workflow

```python
# Step 1: Estimate
estimate = xquik_fetch("/extractions/estimate", method="POST", json_body={
    "toolType": "reply_extractor",
    "targetTweetId": "1893704267862470862",
})

if not estimate["allowed"]:
    print(f"Estimate requires {estimate['creditsRequired']}; available {estimate['creditsAvailable']}")
    exit()

# Step 2: Create job
job = xquik_fetch("/extractions", method="POST", json_body={
    "toolType": "reply_extractor",
    "targetTweetId": "1893704267862470862",
})

# Step 3: Poll until complete (large jobs may return "running")
while job["status"] in ("pending", "running"):
    time.sleep(2)
    job = xquik_fetch(f"/extractions/{job['id']}")

# Step 4: Get results
cursor = None
results = []

while True:
    path = f"/extractions/{job['id']}"
    if cursor:
        path += f"?after={cursor}"
    page = xquik_fetch(path)
    results.extend(page["results"])

    if not page["hasMore"]:
        break
    cursor = page["nextCursor"]

print(f"Extracted {len(results)} results")
```

## Giveaway Draw

```python
# Create draw with all filters
draw = xquik_fetch("/draws", method="POST", json_body={
    "tweetUrl": "https://x.com/burakbayir/status/1893456789012345678",
    "winnerCount": 3,
    "backupCount": 2,
    "uniqueAuthorsOnly": True,
    "mustRetweet": True,
    "mustFollowUsername": "burakbayir",
    "filterMinFollowers": 50,
    "filterAccountAgeDays": 30,
    "requiredKeywords": ["giveaway"],
})

# Get winners
details = xquik_fetch(f"/draws/{draw['id']}")
for winner in details["winners"]:
    role = "BACKUP" if winner["isBackup"] else "WINNER"
    print(f"{role} #{winner['position']}: @{winner['authorUsername']}")
```

## Webhook Handler (Python Standard Library)

```python
import hashlib
import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

def load_secret(name: str) -> str:
    """Read from your runtime secret store."""
    raise RuntimeError(f"Configure {name} in your secret store.")

# Per-webhook secret from POST /webhooks response, not a Xquik account credential
WEBHOOK_SECRET = load_secret("XQUIK_WEBHOOK_SECRET")
processed_hashes = set()  # Use Redis/DB in production

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

EVENT_HANDLERS = {
    "tweet.new": lambda u, d: print(f"New tweet from @{u}: {d['text']}"),
    "tweet.reply": lambda u, d: print(f"Reply from @{u}: {d['text']}"),
    "tweet.quote": lambda u, d: print(f"Quote from @{u}: {d['text']}"),
    "tweet.retweet": lambda u, d: print(f"Retweet by @{u}"),
}

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        signature = self.headers.get("X-Xquik-Signature", "")
        payload = self.rfile.read(length)

        if not verify_signature(payload, signature, WEBHOOK_SECRET):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        payload_hash = hashlib.sha256(payload).hexdigest()
        if payload_hash in processed_hashes:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Already processed")
            return
        processed_hashes.add(payload_hash)

        event = json.loads(payload)
        handler = EVENT_HANDLERS.get(event["eventType"])
        if handler:
            handler(event["username"], event["data"])

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

HTTPServer(("", 3000), WebhookHandler).serve_forever()
```
