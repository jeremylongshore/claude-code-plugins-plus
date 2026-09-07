# Intercom Observability — Worked Examples

End-to-end scenarios that wire the individual layers from
[`implementation.md`](implementation.md) into a running integration. Each example
shows the input situation, the code that instruments it, and the resulting
metrics / traces / log lines you should observe.

## Example 1: Instrument a contact lookup end-to-end

**Goal:** every `contacts.find` call is counted, timed, traced, and logged with PII
redacted.

```typescript
const rawClient = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
const client = instrumentedClient(rawClient); // Step 2 proxy adds metrics

async function lookupContact(contactId: string) {
  const start = Date.now();
  const contact = await tracedIntercomCall(       // Step 4 tracing
    "contacts.find",
    { "intercom.contact_id": contactId },
    () => client.contacts.find({ contactId })     // Step 2 metrics fire here
  );
  logIntercomOp("contacts.find", { contact }, Date.now() - start); // Step 3 log
  return contact;
}
```

**Observed output:**

- Counter `intercom_api_requests_total{endpoint="contacts.find",status="success"}` increments by 1.
- Histogram `intercom_api_request_duration_seconds{endpoint="contacts.find"}` records the latency.
- A span `intercom.contacts.find` appears in your tracing backend with `intercom.contact_id`.
- A log line: `{"service":"intercom","operation":"contacts.find","duration_ms":142,"contact":{"id":"...","role":"user"}}` (email/name/phone redacted by the Step 3 serializer).

## Example 2: A rate-limit (429) event

**Goal:** confirm the instrumentation reacts correctly when Intercom returns 429.

When `client.contacts.list()` throws an `IntercomError` with `statusCode === 429`,
the Step 2 proxy runs:

- `intercom_api_requests_total{...,status="error"}` +1
- `intercom_api_errors_total{error_code="rate_limited",status_code="429"}` +1
- `intercom_rate_limit_remaining` is set to `0`

The `IntercomRateLimitLow` alert (`intercom_rate_limit_remaining < 1000`) fires
after 1m, and `IntercomHighErrorRate` fires if the 429s push the error ratio over 5%.

## Example 3: Webhook processing with success/failure accounting

```typescript
async function handleWebhook(payload: { topic: string; id: string; data: unknown }) {
  const start = Date.now();
  try {
    await processWebhook(payload);
    webhookProcessed.inc({ topic: payload.topic, status: "processed" });
    logWebhook(payload.topic, payload.id, "processed", Date.now() - start);
  } catch (err) {
    webhookProcessed.inc({ topic: payload.topic, status: "failed" });
    logWebhook(payload.topic, payload.id, "failed", Date.now() - start);
    throw err;
  }
}
```

If more than 10% of webhooks for any topic fail over 5m, the
`IntercomWebhookFailures` alert fires.

## Example 4: Scraping the metrics endpoint

With the Step 6 `/metrics` route mounted, a Prometheus scrape returns:

```
# HELP intercom_api_requests_total Total Intercom API requests
# TYPE intercom_api_requests_total counter
intercom_api_requests_total{endpoint="contacts.find",method="API",status="success"} 128
intercom_api_errors_total{endpoint="contacts.list",error_code="rate_limited",status_code="429"} 3
intercom_rate_limit_remaining 8420
```

Point a Grafana panel at `intercom_rate_limit_remaining` and the alert rules from
Step 5 at the same series to close the loop from metric to page.
