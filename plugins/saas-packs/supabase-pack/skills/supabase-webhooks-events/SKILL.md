---
name: supabase-webhooks-events
description: 'Implement Supabase database webhooks, pg_net async HTTP, LISTEN/NOTIFY,

  and Edge Function event handlers with signature verification.

  Use when setting up database webhooks for INSERT/UPDATE/DELETE events,

  sending HTTP requests from PostgreSQL triggers, handling Realtime

  postgres_changes as an event source, or building event-driven architectures.

  Trigger with phrases like "supabase webhook", "database events",

  "pg_net trigger", "supabase LISTEN NOTIFY", "webhook signature verify",

  "supabase event-driven", "supabase_functions.http_request".

  '
allowed-tools: Write, Bash(supabase:*), Bash(curl:*), Bash(psql:*)
version: 1.53.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- webhooks
- events
- triggers
- pg_net
- realtime
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Supabase Webhooks & Database Events

## Overview

Supabase offers four complementary event mechanisms: **Database Webhooks** (trigger-based HTTP calls via `pg_net`), **`supabase_functions.http_request()`** (call Edge Functions from triggers), **Postgres LISTEN/NOTIFY** (lightweight pub/sub), and **Realtime `postgres_changes`** (client-side event subscriptions). This skill covers all four patterns with production-ready code including signature verification, idempotency, and retry handling.

## Prerequisites

- Supabase project (local or hosted) with `supabase` CLI installed
- `pg_net` extension enabled: Dashboard > Database > Extensions > search "pg_net" > Enable
- `@supabase/supabase-js` v2+ installed for client-side patterns
- Edge Functions deployed for webhook receiver patterns

## Authentication

Both directions of a webhook are authenticated:

- **Outbound (trigger → Edge Function):** the trigger sends an `Authorization: Bearer <service_role_key>` header. Store the key in a Postgres setting (`app.settings.service_role_key`) or Supabase Vault — never inline it in a committed migration.
- **Inbound (Edge Function receiver):** verify an HMAC-SHA256 signature against a shared `WEBHOOK_SECRET` (read from `Deno.env`) using a constant-time comparison, and reject mismatches with `401`. See [signature-verification.md](references/signature-verification.md).

## Instructions

Pick the mechanism that fits the consumer: `pg_net` triggers for server-side HTTP fan-out, Edge Function receivers for signed processing, LISTEN/NOTIFY for in-database pub/sub, and Realtime for client UI. Write each SQL trigger to a `supabase/migrations/` file and each handler to `supabase/functions/<name>/index.ts`, then apply and deploy with the `supabase` CLI.

### Step 1 — Database Webhooks with `pg_net` and Trigger Functions

Enable `pg_net`, then write a trigger function that POSTs the changed row to an Edge Function. Attach it `AFTER INSERT/UPDATE/DELETE`. Full trigger set (conditional status-change trigger, the `supabase_functions.http_request()` built-in helper, and `net._http_response` inspection queries) is in [database-webhooks.md](references/database-webhooks.md).

```sql
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

CREATE OR REPLACE FUNCTION public.notify_order_created()
RETURNS trigger AS $$
BEGIN
  PERFORM net.http_post(
    url     := 'https://<project-ref>.supabase.co/functions/v1/on-order-created',
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body    := jsonb_build_object('type', TG_OP, 'record', row_to_json(NEW)::jsonb)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_order_created
  AFTER INSERT ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_order_created();
```

### Step 2 — Edge Function Webhook Receivers with Signature Verification

Write an Edge Function that reads the raw body, verifies the HMAC signature, parses the typed payload, and routes by event type. Guard against duplicate delivery with a `processed_events` idempotency table. The complete receiver, the idempotent-handler variant, and the idempotency table DDL are in [edge-function-receivers.md](references/edge-function-receivers.md).

```typescript
// supabase/functions/on-order-created/index.ts
serve(async (req) => {
  const rawBody = await req.text();
  const secret = Deno.env.get("WEBHOOK_SECRET");
  if (secret) {
    const sig = req.headers.get("x-webhook-signature") ?? "";
    if (!(await verifySignature(rawBody, sig, secret)))
      return new Response(JSON.stringify({ error: "Invalid signature" }), { status: 401 });
  }
  const payload = JSON.parse(rawBody); // { type, table, record, old_record }
  // route by payload.type: INSERT | UPDATE | DELETE
  return new Response(JSON.stringify({ received: true }));
});
```

### Step 3 — Postgres LISTEN/NOTIFY and Realtime as Event Source

Use `pg_notify` from a trigger for lightweight, non-persistent pub/sub consumed by a backend `LISTEN`; use Realtime `postgres_changes` for client-side UI subscriptions (keep NOTIFY payloads to IDs — they truncate past 8000 bytes). The backend listener, the full Realtime subscription with event routing, and the combined event-driven architecture diagram are in [listen-notify-realtime.md](references/listen-notify-realtime.md).

```typescript
const channel = supabase
  .channel("orders-events")
  .on("postgres_changes",
    { event: "*", schema: "public", table: "orders" },
    (payload) => console.log(payload.eventType, payload.new))
  .subscribe();
```

## Output

These patterns produce:

- Database trigger functions calling Edge Functions via `pg_net` on row changes
- Conditional triggers that fire only when specific columns change
- Edge Function webhook receivers with HMAC signature verification
- Idempotent event processing preventing duplicate side effects
- LISTEN/NOTIFY channels for lightweight inter-service communication
- Realtime subscriptions for live client-side UI updates
- An event-driven architecture combining server and client patterns

## Error Handling

| Error | Cause | Fix |
| ------- | ------- | ----- |
| `pg_net` returns 404 | Edge Function not deployed or wrong URL | Run `supabase functions deploy <name>` and verify the URL matches |
| Webhook not firing | Trigger not attached or table not in publication | Check `SELECT * FROM pg_trigger WHERE tgrelid = 'orders'::regclass;` |
| Duplicate events processed | No idempotency layer | Add `processed_events` table with unique `event_id` constraint |
| Realtime not receiving | Table not added to Realtime publication | Dashboard > Database > Replication > enable the table |
| `net._http_response` shows 401 | Invalid or missing auth header | Verify `service_role_key` is set in `app.settings` or vault |
| NOTIFY payload truncated | Payload exceeds 8000 bytes | Send only IDs in NOTIFY, fetch full record in the listener |
| Auth hook errors | Function raises exception | Check Dashboard > Logs > Auth; ensure function returns valid JSONB |
| Trigger silently fails | `SECURITY DEFINER` without `search_path` | Add `SET search_path = public, extensions;` to function |

## Examples

- [database-webhooks.md](references/database-webhooks.md) — full `pg_net` trigger set: conditional status-change trigger, the `supabase_functions.http_request()` helper, and `net._http_response` inspection queries.
- [edge-function-receivers.md](references/edge-function-receivers.md) — complete signed Edge Function receiver, idempotent handler, and idempotency-table DDL.
- [listen-notify-realtime.md](references/listen-notify-realtime.md) — backend `LISTEN` client, full Realtime subscription, and the combined event-driven architecture diagram.
- [examples.md](references/examples.md) — local webhook testing with ngrok and curl.
- [signature-verification.md](references/signature-verification.md) — Node.js HMAC signature verification.
- [event-handler-pattern.md](references/event-handler-pattern.md) — a typed event dispatcher pattern.

## Resources

- [Database Webhooks](https://supabase.com/docs/guides/database/webhooks) — configure via Dashboard or SQL
- [pg_net Extension](https://supabase.com/docs/guides/database/extensions/pg_net) — async HTTP from PostgreSQL
- [Edge Functions](https://supabase.com/docs/guides/functions) — Deno-based serverless handlers
- [Realtime postgres_changes](https://supabase.com/docs/guides/realtime/postgres-changes) — client-side subscriptions
- [Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks) — custom JWT claims and login events
- [supabase-js Reference](https://supabase.com/docs/reference/javascript/subscribe) — `channel().on()` API

## Next Steps

For performance optimization of triggers and queries, see `supabase-performance-tuning`. For production hardening including RLS policies on webhook-accessed tables, see `supabase-security-basics`.
