---
name: supabase-webhooks-events
description: |
  Implement Supabase database webhooks, pg_net async HTTP, and Edge Function event handlers.
  Use when setting up database webhooks for INSERT/UPDATE/DELETE events,
  sending HTTP requests from PostgreSQL triggers, or handling events in Edge Functions.
  Trigger with phrases like "supabase webhook", "supabase events",
  "database webhook", "pg_net", "supabase trigger HTTP".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, webhooks, events, triggers]

---
# Supabase Webhooks & Events

## Overview
Supabase provides three event mechanisms: Database Webhooks (built-in UI for table events), `pg_net` (async HTTP from SQL triggers), and Edge Functions as event handlers. This skill covers all three patterns with real implementation code.

## Prerequisites
- Supabase project with dashboard access
- `pg_net` extension enabled (Dashboard > Database > Extensions)

## Instructions

### Pattern 1: Database Webhooks (Dashboard)

Configure in Dashboard > Database > Webhooks:
1. Select table and event (INSERT, UPDATE, DELETE)
2. Set the webhook URL (your Edge Function or external endpoint)
3. Add HTTP headers (e.g., Authorization)

The webhook payload is:

```json
{
  "type": "INSERT",
  "table": "orders",
  "record": { "id": 1, "total": 99.99, "status": "new" },
  "schema": "public",
  "old_record": null
}
```

### Pattern 2: pg_net — Async HTTP from PostgreSQL

```sql
-- Enable the pg_net extension
create extension if not exists pg_net;

-- Create a trigger that sends HTTP requests on INSERT
create or replace function public.notify_order_created()
returns trigger as $$
begin
  -- pg_net.http_post is async and non-blocking
  perform net.http_post(
    url := 'https://<project-ref>.supabase.co/functions/v1/process-order',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.service_role_key', true)
    ),
    body := jsonb_build_object(
      'order_id', new.id,
      'total', new.total,
      'customer_id', new.customer_id
    )
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_order_created
  after insert on public.orders
  for each row execute function public.notify_order_created();
```

```sql
-- Send a GET request
select net.http_get(
  'https://api.example.com/status',
  headers := '{"Authorization": "Bearer token123"}'::jsonb
);

-- Check response (responses stored for 6 hours)
select * from net._http_response order by created desc limit 5;
```

### Pattern 3: Edge Function as Event Handler

```typescript
// supabase/functions/process-order/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface WebhookPayload {
  type: 'INSERT' | 'UPDATE' | 'DELETE'
  table: string
  record: Record<string, any>
  old_record: Record<string, any> | null
}

serve(async (req) => {
  const payload: WebhookPayload = await req.json()

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  switch (payload.type) {
    case 'INSERT': {
      console.log('New order:', payload.record.id)
      // Send confirmation email, update inventory, etc.
      await supabase
        .from('order_events')
        .insert({
          order_id: payload.record.id,
          event_type: 'created',
          metadata: payload.record,
        })
      break
    }
    case 'UPDATE': {
      const oldStatus = payload.old_record?.status
      const newStatus = payload.record.status
      if (oldStatus !== newStatus) {
        console.log(`Order ${payload.record.id}: ${oldStatus} -> ${newStatus}`)
        // Notify customer of status change
      }
      break
    }
    case 'DELETE': {
      console.log('Order deleted:', payload.old_record?.id)
      break
    }
  }

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### Pattern 4: Idempotent Event Processing

```typescript
// Prevent duplicate processing with idempotency keys
serve(async (req) => {
  const payload: WebhookPayload = await req.json()
  const eventId = `${payload.table}-${payload.type}-${payload.record.id}`

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Check if already processed
  const { data: existing } = await supabase
    .from('processed_events')
    .select('id')
    .eq('event_id', eventId)
    .maybeSingle()

  if (existing) {
    return new Response(JSON.stringify({ skipped: true }), { status: 200 })
  }

  // Process the event
  // ... your logic here ...

  // Mark as processed
  await supabase
    .from('processed_events')
    .insert({ event_id: eventId, processed_at: new Date().toISOString() })

  return new Response(JSON.stringify({ success: true }))
})
```

### Pattern 5: Auth Hooks (Login/Signup Events)

```sql
-- Supabase Auth hooks fire on auth events
-- Configure in Dashboard > Auth > Hooks

-- Custom claims hook (modifies JWT on login)
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb as $$
declare
  user_role text;
begin
  select role into user_role
  from public.user_roles
  where user_id = (event->>'user_id')::uuid;

  -- Add custom claim to JWT
  event := jsonb_set(
    event,
    '{claims,user_role}',
    to_jsonb(coalesce(user_role, 'user'))
  );

  return event;
end;
$$ language plpgsql stable;
```

## Output
- Database webhook configured for table events
- `pg_net` trigger sending async HTTP on row changes
- Edge Function handling webhook payloads with type safety
- Idempotency layer preventing duplicate event processing
- Auth hooks modifying JWT claims on login

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Table not in publication | Enable Realtime on table in Dashboard |
| `pg_net` 404 response | Wrong Edge Function URL | Verify function is deployed and URL is correct |
| Duplicate events processed | No idempotency check | Add `processed_events` table pattern |
| Auth hook errors | Function throws exception | Check Supabase Logs > Auth for hook errors |
| `net._http_response` full | Responses accumulate | Responses auto-expire after 6 hours |

## Resources
- [Database Webhooks](https://supabase.com/docs/guides/database/webhooks)
- [pg_net Extension](https://supabase.com/docs/guides/database/extensions/pg_net)
- [Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)
- [Edge Functions](https://supabase.com/docs/guides/functions)

## Next Steps
For performance optimization, see `supabase-performance-tuning`.
