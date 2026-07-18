# Intercom Security — Implementation Reference

Full, copy-paste implementations for the four security controls summarized in
`SKILL.md`. Each section is self-contained.

## Webhook Signature Verification (X-Hub-Signature)

Intercom signs webhook notifications with HMAC-SHA1 using `X-Hub-Signature`. You
must verify this on every incoming webhook, using the raw request body and a
timing-safe comparison.

```typescript
import crypto from "crypto";
import express from "express";

function verifyIntercomWebhook(
  payload: Buffer,
  signature: string,
  secret: string
): boolean {
  // Intercom uses X-Hub-Signature with HMAC-SHA1
  const expectedSignature = "sha1=" + crypto
    .createHmac("sha1", secret)
    .update(payload)
    .digest("hex");

  // Timing-safe comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

const app = express();

app.post(
  "/webhooks/intercom",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["x-hub-signature"] as string;

    if (!signature) {
      return res.status(401).json({ error: "Missing signature" });
    }

    if (!verifyIntercomWebhook(req.body, signature, process.env.INTERCOM_WEBHOOK_SECRET!)) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());
    // Process verified webhook...
    res.status(200).json({ received: true });
  }
);
```

**Key points:**

- Register the route with `express.raw({ type: "application/json" })` so the
  signature is computed over the exact bytes Intercom signed. Parsing to JSON
  first (with `express.json()`) re-serializes the body and breaks the HMAC.
- Reject requests with a missing `X-Hub-Signature` header (`401`) before any
  processing.
- Always use `crypto.timingSafeEqual` — a plain `===` comparison leaks timing
  information an attacker can exploit to forge a signature byte-by-byte.

## Identity Verification (User Hash)

Intercom Identity Verification prevents impersonation by requiring an HMAC of the
user's identifier. Generate the hash server-side only — never expose the identity
secret to the browser.

```typescript
import crypto from "crypto";

// Server-side: generate user hash
function generateIntercomUserHash(userId: string): string {
  return crypto
    .createHmac("sha256", process.env.INTERCOM_IDENTITY_SECRET!)
    .update(userId)
    .digest("hex");
}

// Pass to frontend for Messenger initialization
app.get("/api/intercom-settings", (req, res) => {
  const userId = req.user.id;
  res.json({
    app_id: process.env.INTERCOM_APP_ID,
    user_id: userId,
    user_hash: generateIntercomUserHash(userId),
  });
});
```

**Key points:**

- The `user_id` you hash must be the same stable identifier you send to Intercom
  when booting the Messenger — mismatched identifiers produce a hash Intercom
  rejects.
- `INTERCOM_IDENTITY_SECRET` is distinct from your access token and webhook
  secret. Rotating one does not rotate the others.

## Token Rotation Procedure

```bash
# 1. Generate new token in Developer Hub
#    Settings > Developer Hub > Your App > Authentication

# 2. Update in secret manager (examples)
# AWS
aws secretsmanager update-secret \
  --secret-id intercom/access-token \
  --secret-string "new_token_here"

# GCP
echo -n "new_token_here" | gcloud secrets versions add intercom-token --data-file=-

# Vault
vault kv put secret/intercom access_token="new_token_here"

# 3. Verify new token
curl -s https://api.intercom.io/me \
  -H "Authorization: Bearer $NEW_TOKEN" | jq '.type'
# Should return "admin"

# 4. Deploy updated config
# 5. Revoke old token in Developer Hub
```

**Order matters:** add the new token to the secret manager and deploy *before*
revoking the old one, so there is never a window where no valid token is live.

## Least-Privilege OAuth Scopes

Only request scopes your app actually needs. Excess scopes widen the blast radius
if a token leaks.

| Use Case | Required Scopes |
|----------|----------------|
| Read contact data only | `Read contacts` |
| Manage conversations | `Read conversations`, `Write conversations` |
| Send messages | `Write messages` |
| Manage Help Center | `Read articles`, `Write articles` |
| Full CRM integration | `Read/write contacts`, `Read/write conversations`, `Read/write tags` |
