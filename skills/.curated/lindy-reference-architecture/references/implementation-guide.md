# Lindy Reference Architecture - Implementation Guide

This guide implements the documented webhook boundary without assuming a public SDK or
control-plane API. Create each trigger in the Lindy dashboard, generate its secret there,
and keep the unique URL and secret in your secret manager.

## Secure Event-Driven Boundary

```text
producer -> authenticated intake -> validator/redactor -> durable queue
         -> static route -> approved Lindy webhook -> delivery receipt
                                              \\-> distinct authenticated callback
```

Use a durable queue when the producer expects a quick acknowledgement. Returning 2xx
before the event is durably recorded can lose work during a crash. Queue consumers must
be idempotent because retries and duplicate delivery are normal distributed-system
conditions.

## Configuration Contract

Store one webhook URL and one trigger secret per route. Store callback authentication
separately.

```typescript
type RouteConfig = Readonly<{
  webhookUrl: string;
  triggerSecret: string;
}>;

type AppConfig = Readonly<{
  ingressSecret: string;
  callbackSecret: string;
  routes: Readonly<Record<'order.created.v1' | 'support.requested.v1', RouteConfig>>;
}>;

function requireSecret(name: string, value: string | undefined): string {
  if (!value || value.trim().length < 16) {
    throw new Error(`${name} is missing or too short`);
  }
  return value;
}

function requireLindyTrigger(name: string, value: string | undefined): string {
  if (!value) throw new Error(`${name} is missing`);
  const parsed = new URL(value);
  if (parsed.protocol !== 'https:' || parsed.hostname !== 'public.lindy.ai') {
    throw new Error(`${name} must be an HTTPS public.lindy.ai webhook`);
  }
  if (!parsed.pathname.startsWith('/api/v1/webhooks/')) {
    throw new Error(`${name} has an unexpected path`);
  }
  return parsed.toString();
}

const config: AppConfig = {
  ingressSecret: requireSecret('EVENT_INGRESS_SECRET', process.env.EVENT_INGRESS_SECRET),
  callbackSecret: requireSecret('CALLBACK_SECRET', process.env.CALLBACK_SECRET),
  routes: {
    'order.created.v1': {
      webhookUrl: requireLindyTrigger(
        'LINDY_ORDER_WEBHOOK_URL',
        process.env.LINDY_ORDER_WEBHOOK_URL,
      ),
      triggerSecret: requireSecret(
        'LINDY_ORDER_TRIGGER_SECRET',
        process.env.LINDY_ORDER_TRIGGER_SECRET,
      ),
    },
    'support.requested.v1': {
      webhookUrl: requireLindyTrigger(
        'LINDY_SUPPORT_WEBHOOK_URL',
        process.env.LINDY_SUPPORT_WEBHOOK_URL,
      ),
      triggerSecret: requireSecret(
        'LINDY_SUPPORT_TRIGGER_SECRET',
        process.env.LINDY_SUPPORT_TRIGGER_SECRET,
      ),
    },
  },
};
```

The hostname check happens before any request can be built. Never select the destination
or secret from request data, and never use a shared `LINDY_WEBHOOK_SECRET` across routes.

## Bounded Intake and Data Minimization

Authenticate the producer, cap the body before parsing, allowlist event names, validate
types and lengths, and enqueue only fields the workflow needs.

```typescript
type AcceptedEvent =
  | { event: 'order.created.v1'; eventId: string; orderId: string; countryCode: string; riskBand: string }
  | { event: 'support.requested.v1'; eventId: string; ticketId: string; category: string };

function shortText(value: unknown, max: number): string | undefined {
  return typeof value === 'string' && value.length > 0 && value.length <= max
    ? value
    : undefined;
}

function parseEvent(body: unknown): AcceptedEvent | undefined {
  if (!body || typeof body !== 'object') return undefined;
  const value = body as Record<string, unknown>;
  const eventId = shortText(value.eventId, 100);
  if (!eventId) return undefined;

  if (value.event === 'order.created.v1') {
    const orderId = shortText(value.orderId, 100);
    const countryCode = shortText(value.countryCode, 2);
    const riskBand = shortText(value.riskBand, 20);
    return orderId && countryCode && riskBand
      ? { event: value.event, eventId, orderId, countryCode, riskBand }
      : undefined;
  }

  if (value.event === 'support.requested.v1') {
    const ticketId = shortText(value.ticketId, 100);
    const category = shortText(value.category, 40);
    return ticketId && category
      ? { event: value.event, eventId, ticketId, category }
      : undefined;
  }

  return undefined;
}
```

Do not forward a producer's raw body. The example intentionally excludes names, email
addresses, credentials, free-form customer text, and callback URLs.

## Durable Queue and Idempotency

The intake handler should follow this transaction boundary:

1. Compare the ingress bearer value using a timing-safe operation.
2. Reject bodies over the configured byte limit before JSON parsing.
3. Parse with `parseEvent`; reject unknown fields according to your schema policy.
4. Insert `{eventId, sanitizedEvent, receivedAt}` into a durable queue with a unique
   constraint on `eventId`.
5. Return `202 Accepted` only after the queue confirms the insert or identifies an
   already accepted duplicate.
6. Log only `eventId`, route name, queue state, and a redacted error class.

An in-memory array is not a durable queue. Use a transactional database outbox or a
managed queue with a documented retention and dead-letter policy.

## Lindy Delivery Boundary

The queue consumer chooses a route from the validated event name. Build the outbound
request only after the URL passed `requireLindyTrigger`, attach only that route's
trigger secret, and send the minimized event.

```typescript
type DeliveryReceipt = Readonly<{
  eventId: string;
  route: AcceptedEvent['event'];
  attempt: number;
  status: 'accepted' | 'retryable' | 'rejected';
  responseCode?: number;
}>;

function classifyResponse(status: number): DeliveryReceipt['status'] {
  if (status >= 200 && status < 300) return 'accepted';
  if (status === 408 || status === 429 || status >= 500) return 'retryable';
  return 'rejected';
}
```

At the transport call, set `Authorization: Bearer <that route's trigger secret>` and
`Content-Type: application/json`. Enforce a short timeout and a retry budget such as
three attempts within five minutes. A rejected response goes to manual review; it must
not loop forever. The receipt records the response class, never the response body,
unique webhook path, event payload, or secret.

## Callback Boundary

If the Lindy workflow calls your application back:

- Use a fixed callback endpoint or an opaque callback ID mapped server-side; do not
  accept an arbitrary callback URL from an event producer.
- Configure Lindy's HTTP Request or callback action with `CALLBACK_SECRET`, not any
  trigger secret.
- Require HTTPS, authenticate before parsing, cap the body, validate the result schema,
  and correlate it to a known event ID.
- Make callback processing idempotent and log only the correlation ID and status.

## Multi-Agent and Scheduled Patterns

Use the same contract even when the Lindy workspace provides agent-to-agent actions:
each specialist gets a bounded schema, minimum data, timeout, result validator, and
failure owner. Verify the exact action names and semantics in the current workspace;
this guide does not promise universal feature availability.

For scheduled workflows, retain a run ledger containing the scheduled window,
execution ID, completion state, and catch-up decision. Never assume that the next run
automatically repairs a missed run.

## Verification Checklist

- Authorized synthetic event creates exactly one expected Lindy task.
- Replaying the same event ID creates no duplicate queue item or task.
- Missing or wrong ingress secret returns an error and creates no queue item.
- Missing or wrong trigger secret produces no accepted task.
- A non-HTTPS or non-`public.lindy.ai` route fails during startup before secret use.
- Oversized, unknown, and malformed events are rejected before enqueue.
- Timeout and 429/5xx responses stop at the retry budget and retain a recovery record.
- Callback requests with the trigger secret are rejected; only the callback secret is
  accepted.
- Logs, traces, queue metadata, and receipts contain no webhook path, secret, customer
  payload, or third-party response body.

## Official References

- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Monitoring Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)
