# Postgres LISTEN/NOTIFY and Realtime as Event Source

## Postgres LISTEN/NOTIFY for Lightweight Pub/Sub

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

## Realtime `postgres_changes` as Client-Side Event Source

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

## Event-Driven Architecture: Combining Patterns

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
