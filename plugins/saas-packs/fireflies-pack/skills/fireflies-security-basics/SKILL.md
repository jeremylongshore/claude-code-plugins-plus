---
name: fireflies-security-basics
description: |
  Apply Fireflies.ai security best practices for API keys and webhook verification.
  Use when securing API keys, verifying webhook signatures,
  or auditing Fireflies.ai security configuration.
  Trigger with phrases like "fireflies security", "fireflies secrets",
  "secure fireflies", "fireflies webhook signature", "fireflies HMAC".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api, security]

---
# Fireflies.ai Security Basics

## Overview
Security essentials for Fireflies.ai: API key management, webhook HMAC-SHA256 signature verification, transcript access controls, and audit practices.

## Prerequisites
- Fireflies.ai API key
- Understanding of environment variables
- HTTPS endpoint for webhooks (required by Fireflies)

## Instructions

### Step 1: Secure API Key Storage
```bash
# .env (NEVER commit)
FIREFLIES_API_KEY=your-api-key
FIREFLIES_WEBHOOK_SECRET=your-16-to-32-char-secret

# .gitignore
.env
.env.local
.env.*.local
```

**Pre-commit hook to catch leaked keys:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
if git diff --cached --name-only | xargs grep -l 'FIREFLIES_API_KEY\s*=' 2>/dev/null; then
  echo "ERROR: Potential API key in commit. Remove before committing."
  exit 1
fi
```

### Step 2: Webhook Signature Verification (HMAC-SHA256)
Fireflies signs webhook payloads with HMAC-SHA256. The signature arrives in the `x-hub-signature` header.

```typescript
import crypto from "crypto";

function verifyFirefliesWebhook(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  // Timing-safe comparison prevents timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Express middleware
import express from "express";
const app = express();

app.post("/webhooks/fireflies",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["x-hub-signature"] as string;
    const payload = req.body.toString();

    if (!signature || !verifyFirefliesWebhook(payload, signature, process.env.FIREFLIES_WEBHOOK_SECRET!)) {
      console.warn("Invalid webhook signature rejected");
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(payload);
    console.log(`Verified webhook: ${event.eventType} for ${event.meetingId}`);
    res.status(200).json({ received: true });
  }
);
```

### Step 3: Configure Webhook Secret
1. Go to [app.fireflies.ai/settings](https://app.fireflies.ai/settings)
2. Select **Developer settings** tab
3. Enter a 16-32 character secret or click **Generate**
4. Store the secret in your environment as `FIREFLIES_WEBHOOK_SECRET`

### Step 4: Python Webhook Verification
```python
import hmac, hashlib, json
from flask import Flask, request, jsonify

app = Flask(__name__)

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.post("/webhooks/fireflies")
def handle_webhook():
    signature = request.headers.get("x-hub-signature", "")
    if not verify_signature(request.data, signature, os.environ["FIREFLIES_WEBHOOK_SECRET"]):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.json
    print(f"Verified: {event['eventType']} for {event['meetingId']}")
    return jsonify({"received": True})
```

### Step 5: Transcript Privacy Levels
Fireflies supports these privacy levels via `updateMeetingPrivacy`:

| Level | Access |
|-------|--------|
| `owner` | Only meeting organizer |
| `participants` | Only meeting participants |
| `teammatesandparticipants` | Workspace members + participants |
| `teammates` | All workspace members |
| `link` | Anyone with the link |

```typescript
// Lock a transcript to participants only
await firefliesQuery(`
  mutation($id: String!, $privacy: String!) {
    updateMeetingPrivacy(transcript_id: $id, privacy_level: $privacy)
  }
`, { id: "transcript-id", privacy: "participants" });
```

### Step 6: API Key Rotation
```bash
set -euo pipefail
# 1. Generate new key in Fireflies dashboard (Integrations > Fireflies API)
# 2. Test new key
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $NEW_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}' | jq '.data.user.email'

# 3. Update environment/secret store
# 4. Verify production
# 5. Old key is automatically invalidated when new one is generated
```

## Security Checklist
- [ ] API key in environment variables, not code
- [ ] `.env` files in `.gitignore`
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] Webhook secret is 16-32 characters
- [ ] Transcript privacy set to `participants` or stricter
- [ ] Pre-commit hook catches key leaks
- [ ] Separate API keys for dev/staging/prod
- [ ] HTTPS required for all webhook endpoints

## Error Handling
| Issue | Detection | Fix |
|-------|-----------|-----|
| Leaked API key | Git scanning, CI alerts | Regenerate immediately in dashboard |
| Invalid webhook signature | 401 from your endpoint | Verify secret matches dashboard |
| Overly permissive privacy | Audit transcript visibility | Set to `participants` default |
| Key rotation gap | Auth failures after rotation | Deploy new key before revoking old |

## Output
- Secure API key storage with leak prevention
- HMAC-SHA256 webhook signature verification
- Privacy-controlled transcript access
- Key rotation procedure

## Resources
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)
- [Fireflies Privacy Settings](https://fireflies.ai/privacy)

## Next Steps
For production deployment, see `fireflies-prod-checklist`.
