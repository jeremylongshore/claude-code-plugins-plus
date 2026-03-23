---
name: supabase-webhooks-events
description: |
  Implement Supabase database webhooks, pg_net async HTTP, LISTEN/NOTIFY,
  and Edge Function event handlers with signature verification.
  Use when setting up database webhooks for INSERT/UPDATE/DELETE events,
  sending HTTP requests from PostgreSQL triggers, handling Realtime
  postgres_changes as an event source, or building event-driven architectures.
  Trigger with phrases like "supabase webhook", "database events",
  "pg_net trigger", "supabase LISTEN NOTIFY", "webhook signature verify",
  "supabase event-driven", "supabase_functions.http_request".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(curl:*), Bash(psql:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, webhooks, events, triggers, pg_net, realtime]
---

# Supabase Webhooks & Database Events

## Overview

Supabase offers four complementary event mechanisms: **Database Webhooks** (trigger-based HTTP calls via `pg_net`), **`supabase_functions.http_request()`** (call Edge Functions from triggers), **Postgres LISTEN/NOTIFY** (lightweight pub/sub), and **Realtime `postgres_changes`** (client-side event subscriptions). This skill covers all four patterns with production-ready code including signature verification, idempotency, and retry handling.

## Prerequisites

- Supabase project (local or hosted) with `supabase` CLI installed
- `pg_net` extension enabled: Dashboard > Database > Extensions > search "pg_net" > Enable
- `@supabase/supabase-js` v2+ installed for client-side patterns
- Edge Functions deployed for webhook receiver patterns

## Step 1 — Database Webhooks with `pg_net` and Trigger Functions

Database webhooks fire HTTP requests when rows change. Under the hood, Supabase uses the `pg_net` extension to make async, non-blocking HTTP calls from within PostgreSQL.

### Enable pg_net and Create the Trigger Function

```sql
-- Enable the pg_net extension (one-time)
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- Trigger function: POST to an Edge Function on every new order
CREATE OR REPLACE FUNCTION public.notify_order_created()
RETURNS trigger AS $$
BEGIN
  PERFORM net.http_post(
    url    := 'https://<project-ref>.supabase.co/functions/v1/on-order-created',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key', true)
    ),
    body   := jsonb_build_object(
      'table',  TG_TABLE_NAME,
      'type',   TG_OP,
      'record', row_to_json(NEW)::jsonb,
      'old_record', CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD)::jsonb ELSE NULL END
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Attach Triggers for INSERT, UPDATE, DELETE

```sql
-- Fire on new rows
CREATE TRIGGER on_order_created
  AFTER INSERT ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_order_created();

-- Fire on status changes only (conditional trigger)
CREATE OR REPLACE FUNCTION public.notify_order_status_changed()
RETURNS trigger AS $$
BEGIN
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    PERFORM net.http_post(
      url    := 'https://<project-ref>.supabase.co/functions/v1/on-status-change',
      headers := '{"Content-Type": "application/json"}'::jsonb,
      body   := jsonb_build_object(
        'order_id',   NEW.id,
        'old_status', OLD.status,
        'new_status', NEW.status,
        'changed_at', now()
      )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_order_status_changed
  AFTER UPDATE ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_order_status_changed();
```

### Using `supabase_functions.http_request()` (Built-in Helper)

Supabase provides a built-in wrapper that simplifies calling Edge Functions from triggers without managing headers manually:

```sql
-- This is the function Supabase auto-creates for Dashboard-configured webhooks
-- You can also call it directly in your own trigger functions
CREATE TRIGGER on_profile_updated
  AFTER UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION supabase_functions.http_request(
    'https://<project-ref>.supabase.co/functions/v1/on-profile-update',
    'POST',
    '{"Content-Type": "application/json"}',
    '{}',  -- params
    '5000' -- timeout ms
  );
```

### Inspect pg_net Responses

```sql
-- Check recent HTTP responses (retained for 6 hours)
SELECT id, status_code, content, created
FROM net._http_response
ORDER BY created DESC
LIMIT 10;

-- Find failed requests
SELECT id, status_code, content
FROM net._http_response
WHERE status_code >= 400
ORDER BY created DESC;
```

## Step 2 — Edge Function Webhook Receivers with Signature Verification

### Webhook Receiver with Signature Verification

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

### Idempotent Event Processing

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

## Step 3 — Postgres LISTEN/NOTIFY and Realtime as Event Source

### Postgres LISTEN/NOTIFY for Lightweight Pub/Sub

LISTEN/NOTIFY is PostgreSQL's built-in pub/sub. It does not persist messages and is best for ephemeral notifications between database functions or connected clients:

```sql
-- Trigger function that emits a NOTIFY on row change
CREATE OR REPLACE FUNCTION public.notify_changes()
RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify(
    'db_changes',
    json_build_object(
      'table', TG_TABLE_NAME,
      'op',    TG_OP,
      'id',    COALESCE(NEW.id, OLD.id)
    )::text
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER orders_notify
  AFTER INSERT OR UPDATE OR DELETE ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_changes();
```

```typescript
// Listen from a Node.js backend using pg driver
import { Client } from "pg";

const client = new Client({ connectionString: process.env.DATABASE_URL });
await client.connect();

await client.query("LISTEN db_changes");

client.on("notification", (msg) => {
  const payload = JSON.parse(msg.payload!);
  console.log(`${payload.op} on ${payload.table}: id=${payload.id}`);
});
```

### Realtime `postgres_changes` as Client-Side Event Source

Supabase Realtime lets frontend clients subscribe to database changes without polling. Enable Realtime on your table first (Dashboard > Database > Replication).

```typescript
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Subscribe to all changes on the orders table
const channel = supabase
  .channel("orders-events")
  .on(
    "postgres_changes",
    {
      event: "*",           // or 'INSERT' | 'UPDATE' | 'DELETE'
      schema: "public",
      table: "orders",
      filter: "status=eq.pending",  // optional: RLS-style filter
    },
    (payload) => {
      console.log("Change type:", payload.eventType);
      console.log("New row:", payload.new);
      console.log("Old row:", payload.old);

      // React to the change
      switch (payload.eventType) {
        case "INSERT":
          showToast(`New order #${payload.new.id}`);
          break;
        case "UPDATE":
          updateOrderInUI(payload.new);
          break;
        case "DELETE":
          removeOrderFromUI(payload.old.id);
          break;
      }
    }
  )
  .subscribe((status) => {
    console.log("Subscription status:", status);
  });

// Cleanup when done
// await supabase.removeChannel(channel);
```

### Event-Driven Architecture: Combining Patterns

Use database triggers for server-side workflows and Realtime for client-side UI updates:

```
┌──────────────┐     INSERT      ┌──────────────────┐
│   Client     │ ──────────────► │  orders table     │
│  (browser)   │                 └────────┬─────────┘
│              │                          │
│  Realtime ◄──┼──── postgres_changes ────┤
│  (UI update) │                          │
└──────────────┘                          │ AFTER INSERT trigger
                                          ▼
                                 ┌──────────────────┐
                                 │  pg_net HTTP POST │
                                 │  → Edge Function  │
                                 └────────┬─────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │  Send email       │
                                 │  Update inventory │
                                 │  Log to audit     │
                                 └──────────────────┘
```

## Output

After implementing these patterns you will have:

- Database trigger functions calling Edge Functions via `pg_net` on row changes
- Conditional triggers that fire only when specific columns change
- Edge Function webhook receivers with HMAC signature verification
- Idempotent event processing preventing duplicate side effects
- LISTEN/NOTIFY channels for lightweight inter-service communication
- Realtime subscriptions for live client-side UI updates
- An event-driven architecture combining server and client patterns

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `pg_net` returns 404 | Edge Function not deployed or wrong URL | Run `supabase functions deploy <name>` and verify the URL matches |
| Webhook not firing | Trigger not attached or table not in publication | Check `SELECT * FROM pg_trigger WHERE tgrelid = 'orders'::regclass;` |
| Duplicate events processed | No idempotency layer | Add `processed_events` table with unique `event_id` constraint |
| Realtime not receiving | Table not added to Realtime publication | Dashboard > Database > Replication > enable the table |
| `net._http_response` shows 401 | Invalid or missing auth header | Verify `service_role_key` is set in `app.settings` or vault |
| NOTIFY payload truncated | Payload exceeds 8000 bytes | Send only IDs in NOTIFY, fetch full record in the listener |
| Auth hook errors | Function raises exception | Check Dashboard > Logs > Auth; ensure function returns valid JSONB |
| Trigger silently fails | `SECURITY DEFINER` without `search_path` | Add `SET search_path = public, extensions;` to function |

## Examples

See [examples.md](references/examples.md) for local webhook testing with ngrok and curl.

See [signature-verification.md](references/signature-verification.md) for Node.js HMAC signature verification.

See [event-handler-pattern.md](references/event-handler-pattern.md) for a typed event dispatcher pattern.

## Resources

- [Database Webhooks](https://supabase.com/docs/guides/database/webhooks) — configure via Dashboard or SQL
- [pg_net Extension](https://supabase.com/docs/guides/database/extensions/pg_net) — async HTTP from PostgreSQL
- [Edge Functions](https://supabase.com/docs/guides/functions) — Deno-based serverless handlers
- [Realtime postgres_changes](https://supabase.com/docs/guides/realtime/postgres-changes) — client-side subscriptions
- [Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks) — custom JWT claims and login events
- [supabase-js Reference](https://supabase.com/docs/reference/javascript/subscribe) — `channel().on()` API

## Next Steps

For performance optimization of triggers and queries, see `supabase-performance-tuning`. For production hardening including RLS policies on webhook-accessed tables, see `supabase-security-basics`.
