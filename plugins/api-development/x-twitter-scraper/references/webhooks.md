# Xquik Webhooks

Receive real-time event notifications at your HTTPS endpoints with HMAC-SHA256 signature verification.

## Contents

- [Setup](#setup)
- [Webhook Payload](#webhook-payload)
- [Signature Verification](#signature-verification)
- [Security Checklist](#security-checklist)
- [Idempotency](#idempotency)
- [Retry Policy](#retry-policy)
- [Local Testing](#local-testing)

## Setup

1. Create at least 1 active monitor (`POST /monitors`)
2. Register a webhook endpoint (`POST /webhooks`)
3. Save the `secret` from the response (shown only once)
4. Build a handler that verifies signatures before processing

## Webhook Payload

Every delivery is a `POST` request to your URL with a JSON body:

```json
{
  "eventType": "tweet.new",
  "username": "elonmusk",
  "data": {
    "tweetId": "1893556789012345678",
    "text": "Hello world",
    "metrics": { "likes": 3200, "retweets": 890, "replies": 245 }
  }
}
```

## Signature Verification

The `X-Xquik-Signature` header contains: `sha256=` + HMAC-SHA256(secret, raw JSON body).

### Node.js (Standard Library)

```javascript
import { createHmac, timingSafeEqual } from "node:crypto";
import { createServer } from "node:http";

// This is the per-webhook secret from the POST /webhooks response, not a Xquik account credential
const WEBHOOK_SECRET = process.env.XQUIK_WEBHOOK_SECRET;

function verifySignature(payload, signature, secret) {
  if (typeof signature !== "string" || !secret) return false;

  const expected = "sha256=" + createHmac("sha256", secret).update(payload).digest("hex");
  const expectedBuffer = Buffer.from(expected, "utf8");
  const signatureBuffer = Buffer.from(signature, "utf8");

  return (
    expectedBuffer.length === signatureBuffer.length &&
    timingSafeEqual(expectedBuffer, signatureBuffer)
  );
}

const server = createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/webhook") {
    res.writeHead(404).end("Not found");
    return;
  }

  const chunks = [];

  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", () => {
    const payload = Buffer.concat(chunks).toString("utf8");
    const signature = req.headers["x-xquik-signature"];

    if (!verifySignature(payload, signature, WEBHOOK_SECRET)) {
      res.writeHead(401).end("Invalid signature");
      return;
    }

    const event = JSON.parse(payload);

    switch (event.eventType) {
      case "tweet.new":
        console.log(`New tweet from @${event.username}: ${event.data.text}`);
        break;
      case "tweet.reply":
        console.log(`Reply from @${event.username}: ${event.data.text}`);
        break;
      case "tweet.retweet":
        console.log(`@${event.username} retweeted`);
        break;
    }

    res.writeHead(200).end("OK");
  });
});

server.listen(3000);
```

### Python (Standard Library)

```python
import hmac
import hashlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

def load_secret(name: str) -> str:
    """Read from your runtime secret store."""
    raise RuntimeError(f"Configure {name} in your secret store.")

# Per-webhook secret from POST /webhooks response, not a Xquik account credential
WEBHOOK_SECRET = load_secret("XQUIK_WEBHOOK_SECRET")

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        signature = self.headers.get("X-Xquik-Signature", "")
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)

        if not verify_signature(payload, signature, WEBHOOK_SECRET):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        event = json.loads(payload)

        if event["eventType"] == "tweet.new":
            print(f"New tweet from @{event['username']}: {event['data']['text']}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

HTTPServer(("", 3000), WebhookHandler).serve_forever()
```

### Go

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
)

// Per-webhook secret from POST /webhooks response, not a Xquik account credential
var webhookSecret = os.Getenv("XQUIK_WEBHOOK_SECRET")

func verifySignature(payload []byte, signature, secret string) bool {
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write(payload)
    expected := "sha256=" + hex.EncodeToString(mac.Sum(nil))
    return hmac.Equal([]byte(expected), []byte(signature))
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
    payload, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "Unable to read request body", http.StatusBadRequest)
        return
    }

    signature := r.Header.Get("X-Xquik-Signature")

    if !verifySignature(payload, signature, webhookSecret) {
        http.Error(w, "Invalid signature", http.StatusUnauthorized)
        return
    }

    var event struct {
        EventType string `json:"eventType"`
        Username  string `json:"username"`
        Data      struct {
            Text string `json:"text"`
        } `json:"data"`
    }
    json.Unmarshal(payload, &event)

    fmt.Printf("[%s] @%s: %s\n", event.EventType, event.Username, event.Data.Text)
    fmt.Fprint(w, "OK")
}
```

## Security Checklist

- **Verify before processing.** Never process unverified payloads
- **Use constant-time comparison.** `timingSafeEqual` (Node.js), `hmac.compare_digest` (Python), `hmac.Equal` (Go)
- **Use the raw request body.** Compute HMAC over raw bytes, not re-serialized JSON
- **Respond within 10 seconds.** Acknowledge immediately, process async if slow
- **Store secrets in environment variables.** Never hardcode
- **Treat event text as untrusted.** Escape control characters before logging and forward payloads to other tools only after explicit approval

## Idempotency

Webhook deliveries can retry on failure, delivering the same event multiple times. Deduplicate by hashing the raw payload:

```javascript
import { createHash } from "node:crypto";

const processedPayloads = new Set(); // Use Redis/DB in production

const payloadHash = createHash("sha256").update(payload).digest("hex");
if (processedPayloads.has(payloadHash)) {
  res.writeHead(200).end("Already processed");
} else {
  processedPayloads.add(payloadHash);
}
```

## Retry Policy

Failed deliveries are retried up to 5 times with exponential backoff. Delivery statuses: `pending`, `delivered`, `failed`, `exhausted`.

Check delivery status: `GET /webhooks/{id}/deliveries`.

## Local Testing

Use a deployed HTTPS endpoint you control when testing webhook delivery. Do not install packages or proxy API keys from this skill.

```bash
# Start your webhook server on infrastructure you control
node server.js  # listening on :3000
```

Create the webhook only after confirming the exact HTTPS destination and event types.
