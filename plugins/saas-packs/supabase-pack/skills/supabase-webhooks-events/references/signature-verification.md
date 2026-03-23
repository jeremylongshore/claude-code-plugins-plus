# Signature Verification

## Why Verify Webhook Signatures

Any public Edge Function URL can receive HTTP requests from anyone. Without signature verification, an attacker could send fake webhook payloads to trigger unintended side effects (creating orders, modifying data, sending emails). Always verify the HMAC signature before processing.

## Deno (Edge Functions)

```typescript
// Deno-native using Web Crypto API (no npm dependencies)
async function verifyWebhookSignature(
  rawBody: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const encoder = new TextEncoder();

  // Import the secret as an HMAC key
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  // Sign the raw body
  const signed = await crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(rawBody)
  );

  // Convert to hex string
  const expected = Array.from(new Uint8Array(signed))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  // Constant-time comparison to prevent timing attacks
  if (signature.length !== expected.length) return false;
  let mismatch = 0;
  for (let i = 0; i < signature.length; i++) {
    mismatch |= signature.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return mismatch === 0;
}

// Usage in Edge Function
serve(async (req) => {
  const secret = Deno.env.get("WEBHOOK_SECRET")!;
  const body = await req.text();
  const sig = req.headers.get("x-webhook-signature") ?? "";

  if (!(await verifyWebhookSignature(body, sig, secret))) {
    return new Response("Unauthorized", { status: 401 });
  }

  const payload = JSON.parse(body);
  // ... process verified payload
});
```

## Node.js (External Webhook Receivers)

```typescript
import crypto from "node:crypto";

function verifySupabaseSignature(
  rawBody: Buffer | string,
  signature: string,
  timestamp: string,
  secret: string
): boolean {
  // Reject old timestamps (replay attack protection — 5 min window)
  const age = Date.now() - parseInt(timestamp, 10) * 1000;
  if (age > 300_000) {
    console.error("Webhook timestamp too old:", age, "ms");
    return false;
  }

  // Compute expected HMAC using timestamp.body format
  const signedPayload = `${timestamp}.${rawBody.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(signedPayload)
    .digest("hex");

  // Timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Usage in Express
app.post("/webhook/supabase", (req, res) => {
  const signature = req.headers["x-webhook-signature"] as string;
  const timestamp = req.headers["x-webhook-timestamp"] as string;

  if (!verifySupabaseSignature(req.body, signature, timestamp, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const payload = JSON.parse(req.body.toString());
  // ... process verified payload
  res.json({ ok: true });
});
```

## Generating the Webhook Secret

```bash
# Generate a secure random secret
openssl rand -hex 32
# Example: a1b2c3d4e5f6...

# Set as Edge Function secret
supabase secrets set WEBHOOK_SECRET=a1b2c3d4e5f6...

# Set in the trigger function (use Supabase Vault for production)
-- Dashboard > SQL Editor
SELECT vault.create_secret('a1b2c3d4e5f6...', 'webhook_secret');
```

## Signing Outgoing Webhooks from Triggers

If you need the trigger to sign the payload so the receiver can verify:

```sql
CREATE OR REPLACE FUNCTION public.signed_webhook()
RETURNS trigger AS $$
DECLARE
  payload jsonb;
  secret text;
  signature text;
BEGIN
  payload := jsonb_build_object('type', TG_OP, 'record', row_to_json(NEW)::jsonb);

  -- Retrieve secret from Vault
  SELECT decrypted_secret INTO secret
  FROM vault.decrypted_secrets
  WHERE name = 'webhook_secret';

  -- Compute HMAC-SHA256 signature
  signature := encode(
    hmac(payload::text, secret, 'sha256'),
    'hex'
  );

  PERFORM net.http_post(
    url     := 'https://your-receiver.com/webhook',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-webhook-signature', signature
    ),
    body    := payload
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
