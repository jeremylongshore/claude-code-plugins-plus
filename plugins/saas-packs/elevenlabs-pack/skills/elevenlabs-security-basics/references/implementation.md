# ElevenLabs Security — Full Implementation

Deep reference for the ElevenLabs Security Basics skill. Each section is the
production-grade implementation for one step in the workflow. The SKILL.md body
carries the lean skeleton; drill in here for the complete code.

## Step 2: Environment-Specific Keys

Load and validate the API key at startup, and warn loudly if a production key
leaks into a development environment:

```typescript
// src/elevenlabs/config.ts
interface ElevenLabsSecurityConfig {
  apiKey: string;
  webhookSecret: string;
  environment: "development" | "staging" | "production";
}

export function getSecurityConfig(): ElevenLabsSecurityConfig {
  const env = (process.env.NODE_ENV || "development") as ElevenLabsSecurityConfig["environment"];

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    throw new Error("ELEVENLABS_API_KEY is required");
  }

  // Warn if production key is used in dev
  if (env === "development" && apiKey.startsWith("sk_live_")) {
    console.warn("WARNING: Using production API key in development environment");
  }

  return {
    apiKey,
    webhookSecret: process.env.ELEVENLABS_WEBHOOK_SECRET || "",
    environment: env,
  };
}
```

## Step 3: Webhook HMAC Signature Verification

ElevenLabs webhooks include an `ElevenLabs-Signature` header for HMAC
verification. The header format is `t=TIMESTAMP,v1=SIGNATURE`:

```typescript
// src/elevenlabs/webhook-verify.ts
import crypto from "crypto";

/**
 * Verify ElevenLabs webhook signature using HMAC-SHA256.
 * The shared secret is generated when you create a webhook in the dashboard.
 */
export function verifyWebhookSignature(
  payload: string | Buffer,
  signatureHeader: string,
  secret: string
): boolean {
  if (!signatureHeader || !secret) return false;

  // ElevenLabs signature format: t=TIMESTAMP,v1=SIGNATURE
  const parts = signatureHeader.split(",");
  const timestamp = parts.find(p => p.startsWith("t="))?.slice(2);
  const signature = parts.find(p => p.startsWith("v1="))?.slice(3);

  if (!timestamp || !signature) return false;

  // Reject timestamps older than 5 minutes (replay protection)
  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp);
  if (age > 300) {
    console.error("Webhook timestamp too old:", age, "seconds");
    return false;
  }

  // Compute expected HMAC
  const signedPayload = `${timestamp}.${payload.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(signedPayload)
    .digest("hex");

  // Timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, "hex"),
      Buffer.from(expected, "hex")
    );
  } catch {
    return false;
  }
}
```

## Step 4: Express Webhook Endpoint with Verification

Use the raw request body for signature verification, acknowledge fast with a
200, then process asynchronously so you never trip the webhook timeout:

```typescript
import express from "express";
import { verifyWebhookSignature } from "./webhook-verify";

const app = express();

// IMPORTANT: Must use raw body for signature verification
app.post("/webhooks/elevenlabs",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["elevenlabs-signature"] as string;
    const secret = process.env.ELEVENLABS_WEBHOOK_SECRET!;

    if (!verifyWebhookSignature(req.body, signature, secret)) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());

    // Return 200 quickly to acknowledge receipt
    // Process asynchronously to avoid webhook timeout/disable
    res.status(200).json({ received: true });

    processWebhookAsync(event).catch(console.error);
  }
);
```

## Step 5: API Key Rotation Procedure

Rotate keys with zero downtime — validate the new key before cutting over, and
delete the old key only after production is confirmed healthy:

```bash
# 1. Generate new API key in ElevenLabs dashboard
#    Settings > API Keys > Create new key

# 2. Test new key before rotating
curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: sk_new_key_here" | jq '.subscription.tier'

# 3. Update in all environments
# Vercel:
vercel env add ELEVENLABS_API_KEY production

# Fly.io:
fly secrets set ELEVENLABS_API_KEY=sk_new_key_here

# GitHub Actions:
gh secret set ELEVENLABS_API_KEY --body "sk_new_key_here"

# 4. Deploy with new key
# 5. Verify production works
# 6. Delete old key in ElevenLabs dashboard
```

## Step 6: Voice Data Protection

Cloned voices contain biometric data — treat them as PII. Restrict who can
clone, log every operation, and require documented consent:

```typescript
// Cloned voices contain biometric data — treat as PII
const voiceSecurityPolicy = {
  // Restrict who can create/delete cloned voices
  clonePermissions: "admin_only",

  // Log all voice cloning operations
  auditCloning: true,

  // Require consent documentation before cloning
  consentRequired: true,

  // Auto-delete test clones after N days
  testVoiceTtlDays: 30,
};

// Audit log for voice operations
function logVoiceOperation(operation: string, voiceId: string, userId: string) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    type: "elevenlabs.voice.audit",
    operation,  // "clone", "delete", "use"
    voiceId,
    userId,
  }));
}
```
