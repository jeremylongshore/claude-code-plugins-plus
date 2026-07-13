# Event Handler Pattern

## Typed Event Dispatcher

A registry-based pattern for routing Supabase webhook events to typed handlers. This eliminates switch statements and makes adding new event handlers declarative.

```typescript
// types.ts
type EventType = "INSERT" | "UPDATE" | "DELETE";

interface WebhookPayload<T = Record<string, unknown>> {
  type: EventType;
  table: string;
  schema: string;
  record: T;
  old_record: T | null;
}

type EventHandler<T = Record<string, unknown>> = (
  payload: WebhookPayload<T>
) => Promise<void>;

interface HandlerRegistration {
  table: string;
  event: EventType | "*";
  handler: EventHandler;
}
```

## Dispatcher Implementation

```typescript
// event-dispatcher.ts
class EventDispatcher {
  private handlers: HandlerRegistration[] = [];

  on(table: string, event: EventType | "*", handler: EventHandler): void {
    this.handlers.push({ table, event, handler });
  }

  async dispatch(payload: WebhookPayload): Promise<void> {
    const matched = this.handlers.filter(
      (h) =>
        h.table === payload.table &&
        (h.event === "*" || h.event === payload.type)
    );

    if (matched.length === 0) {
      console.warn(
        `No handler for ${payload.type} on ${payload.table}`
      );
      return;
    }

    // Run all matched handlers concurrently
    const results = await Promise.allSettled(
      matched.map((h) => h.handler(payload))
    );

    for (const result of results) {
      if (result.status === "rejected") {
        console.error("Handler failed:", result.reason);
      }
    }
  }
}
```

## Usage

```typescript
// Register handlers
const dispatcher = new EventDispatcher();

dispatcher.on("orders", "INSERT", async (payload) => {
  await sendOrderConfirmationEmail(payload.record.email);
  await updateInventoryCount(payload.record.product_id, -1);
});

dispatcher.on("orders", "UPDATE", async (payload) => {
  if (payload.old_record?.status !== payload.record.status) {
    await notifyStatusChange(payload.record);
  }
});

dispatcher.on("profiles", "*", async (payload) => {
  await syncToExternalCRM(payload.record);
});

// In your Edge Function serve() handler:
serve(async (req) => {
  const payload: WebhookPayload = await req.json();
  await dispatcher.dispatch(payload);
  return new Response(JSON.stringify({ ok: true }));
});
```

## Benefits

- **Type safety**: each handler receives typed payloads
- **Separation of concerns**: one handler per side effect
- **Testable**: handlers are pure async functions, easy to unit test
- **Extensible**: add new handlers without modifying dispatch logic

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
