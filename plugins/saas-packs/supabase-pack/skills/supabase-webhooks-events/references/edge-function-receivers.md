# Edge Function Webhook Receivers with Signature Verification

## Webhook Receiver with Signature Verification

```typescript
// supabase/functions/on-order-created/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

interface WebhookPayload {
  type: "INSERT" | "UPDATE" | "DELETE";
  table: string;
  record: Record<string, unknown>;
  old_record: Record<string, unknown> | null;
}

// Verify webhook signature to prevent spoofing
async function verifySignature(
  body: string,
  signature: string,
  secret: string
): Promise<boolean> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signed = await crypto.subtle.sign("HMAC", key, encoder.encode(body));
  const expected = Array.from(new Uint8Array(signed))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  // Constant-time comparison
  if (signature.length !== expected.length) return false;
  let mismatch = 0;
  for (let i = 0; i < signature.length; i++) {
    mismatch |= signature.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return mismatch === 0;
}

serve(async (req) => {
  // Verify signature if webhook secret is configured
  const webhookSecret = Deno.env.get("WEBHOOK_SECRET");
  const rawBody = await req.text();

  if (webhookSecret) {
    const signature = req.headers.get("x-webhook-signature") ?? "";
    const valid = await verifySignature(rawBody, signature, webhookSecret);
    if (!valid) {
      return new Response(JSON.stringify({ error: "Invalid signature" }), {
        status: 401,
      });
    }
  }

  const payload: WebhookPayload = JSON.parse(rawBody);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  // Route by event type
  switch (payload.type) {
    case "INSERT": {
      console.log(`New ${payload.table} row:`, payload.record.id);

      // Example: log event, send notification, update related table
      await supabase.from("audit_log").insert({
        table_name: payload.table,
        action: "INSERT",
        record_id: payload.record.id,
        payload: payload.record,
      });
      break;
    }
    case "UPDATE": {
      console.log(`Updated ${payload.table}:`, payload.record.id);
      // Compare old and new to detect specific field changes
      if (payload.old_record?.status !== payload.record.status) {
        await supabase.from("notifications").insert({
          user_id: payload.record.user_id,
          message: `Status changed to ${payload.record.status}`,
        });
      }
      break;
    }
    case "DELETE": {
      console.log(`Deleted from ${payload.table}:`, payload.old_record?.id);
      break;
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { "Content-Type": "application/json" },
  });
});
```

## Idempotent Event Processing

Webhooks may be delivered more than once. Use an idempotency table to prevent duplicate processing:

```typescript
// supabase/functions/idempotent-handler/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req) => {
  const payload = await req.json();
  const eventId = `${payload.table}:${payload.type}:${payload.record.id}`;

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // Check if already processed (upsert pattern)
  const { data: existing } = await supabase
    .from("processed_events")
    .select("id")
    .eq("event_id", eventId)
    .maybeSingle();

  if (existing) {
    return new Response(
      JSON.stringify({ skipped: true, reason: "already processed" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }

  // --- Your business logic here ---
  console.log(`Processing event: ${eventId}`);

  // Mark as processed (with TTL for cleanup)
  await supabase.from("processed_events").insert({
    event_id: eventId,
    processed_at: new Date().toISOString(),
  });

  return new Response(JSON.stringify({ processed: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

```sql
-- Idempotency table
CREATE TABLE public.processed_events (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id   text UNIQUE NOT NULL,
  processed_at timestamptz DEFAULT now()
);

-- Auto-cleanup old records (run via pg_cron or scheduled function)
DELETE FROM public.processed_events
WHERE processed_at < now() - interval '7 days';
```
