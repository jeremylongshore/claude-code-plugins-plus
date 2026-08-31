---
name: lindy-webhooks-events
description: 'Configure Lindy AI webhook triggers, callback patterns, and event handling.

  Use when setting up webhook triggers, implementing callback receivers,

  or building event-driven Lindy integrations.

  Trigger with phrases like "lindy webhook", "lindy events",

  "lindy callback", "lindy webhook trigger".

  '
allowed-tools: Read, Write, Edit
version: 1.19.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- webhooks
compatibility: Compatible with AI coding agents that can read and edit application code and Markdown
---
# Lindy Webhooks and Events

## Overview

Build two documented boundaries: an application calls a Lindy **Webhook Received**
trigger using its generated Bearer secret, and Lindy calls an application through
an outbound callback action such as **HTTP Request**. Treat them as separate trust
directions with separate secrets, schemas, retry policies, and evidence.

Use **Read** to inspect the integration and **Write** or **Edit** to implement its
closed contracts. Implement only the documented generated-Bearer trigger and
configurable outbound-request surfaces; do not add unaudited control-plane,
registration, event-feed, or signature mechanisms.

## Prerequisites

- A Webhook Received trigger with its generated URL and nonempty generated secret.
- An approved secret manager; never store secret values in code or skill output.
- A separate, nonempty application-owned callback secret.
- A fixed or strictly allowlisted HTTPS callback destination controlled by the
  application owner.
- Closed request and callback schemas with local field, length, enum, and byte limits.
- A shared atomic idempotency store and durable queue for scaled or retryable work.
- Access to Lindy's Tasks view and synthetic test data with unique request IDs.

## Instructions

### Step 1: Define minimal contracts

Specify only fields the workflow needs. A safe application-owned trigger envelope
might contain `requestId`, an enumerated `eventType`, a non-sensitive `subjectId`,
and `occurredAt`. Reject unknown fields, invalid types, excessive lengths, and
payloads above the documented local byte limit before enqueue or transmission.

Define the callback separately—for example `requestId`, `taskId`, and an enumerated
`status`. Do not return full prompts, model output, source records, or customer data
unless an approved data contract requires those fields.

### Step 2: Configure the Lindy trigger

In the workflow, add **Webhook Received**, create or select a webhook, generate its
secret, and store that secret immediately. Lindy documents URLs in this form:

```text
https://public.lindy.ai/api/v1/webhooks/[unique-id]
```

Callers send `Authorization: Bearer [generated-secret]`. Select the documented
follow-up behavior that matches the workflow: handle in the same task, create a new
task, or ignore follow-ups. Treat request body, headers, and query parameters as
untrusted input. Never copy the full headers object into a prompt or log because it
can contain the Authorization secret.

### Step 3: Validate before attaching the trigger secret

Fail startup unless the URL uses HTTPS, has hostname exactly `public.lindy.ai`, no
unexpected port or embedded credentials, and the expected generated webhook path.
Load a nonempty per-trigger secret only after the destination passes validation.

```typescript
type TriggerConfig = { url: URL; secret: string };

function loadTriggerConfig(env: NodeJS.ProcessEnv): TriggerConfig {
  const url = new URL(env.LINDY_TRIGGER_URL ?? '');
  const path = url.pathname.split('/').filter(Boolean);
  if (
    url.protocol !== 'https:' ||
    url.hostname !== 'public.lindy.ai' ||
    url.port !== '' ||
    url.username !== '' ||
    url.password !== '' ||
    url.search !== '' ||
    url.hash !== '' ||
    path.length !== 4 ||
    path[0] !== 'api' ||
    path[1] !== 'v1' ||
    path[2] !== 'webhooks' ||
    path[3].length === 0
  ) {
    throw new Error('LINDY_TRIGGER_URL is not an approved Lindy webhook URL');
  }

  const secret = env.LINDY_TRIGGER_SECRET ?? '';
  if (secret.length === 0) throw new Error('LINDY_TRIGGER_SECRET is required');
  return { url, secret };
}
```

Do not send the trigger secret to a caller-supplied `callbackUrl`, another Lindy
host, or your own callback receiver.

### Step 4: Deduplicate, queue, and send

Require a stable request ID derived from the source business event. Atomically
reserve that ID and durably enqueue the validated event. A process-local set,
background promise, or timer is not durable and does not coordinate across instances.

The worker sends the closed payload with the generated Bearer secret. Treat 2xx as
transport acceptance only. Treat authentication and other non-retryable 4xx as
permanent failures. Retry only explicitly transient outcomes such as 408, 429, or
selected 5xx with capped exponential backoff, jitter, bounded attempts, and a total
deadline. Reuse the same request ID; dead-letter and alert after exhaustion.

An ambiguous timeout may occur after Lindy accepted the request. Local idempotency
cannot prove exactly-once remote execution, so reconcile the request ID with the
Tasks view or an authenticated callback before retrying or claiming completion.

### Step 5: Configure a distinct authenticated callback

Prefer an application-owned, pre-approved HTTPS callback URL. Configure a Lindy
HTTP Request action to send the closed callback body and:

```text
Authorization: Bearer [application-owned-callback-secret]
Content-Type: application/json
```

The HTTP Request action documentation supports explicit headers and status-code
handling. If using a callback URL from the trigger body, validate it against an
exact scheme/host/path allowlist before any secret-bearing request. If the chosen
callback action cannot enforce that validation and the required Authorization
header, do not use a caller-controlled URL.

At the application receiver, authenticate before inspecting or acting on the body,
enforce a request-byte limit before parsing, validate the closed schema, and use an
atomic `enqueueOnce(requestId, payload)` operation. Return 2xx only after durable
persistence succeeds. Use constant-time secret comparison and never reuse the
Lindy trigger secret as the callback secret.

### Step 6: Corroborate tasks and callbacks

For a synthetic trigger, record its unique request ID and transport result, then
find the corresponding task in Lindy's Tasks view and verify the intended steps and
terminal state. A 2xx trigger response without a matching task is
`ACCEPTED_UNVERIFIED`, not success.

Test a wrong trigger secret: require non-2xx and no task. Test a wrong callback
secret, malformed and oversized callbacks, duplicates, durable-store failure, and
worker termination after enqueue: each must create no unauthorized or duplicate
side effect.

### Step 7: Minimize evidence and telemetry

Record request ID, task ID, status class, attempt, latency, queue disposition, and
sanitized workflow identifier. Do not log secrets, full generated webhook URLs,
headers, full request/response bodies, prompts, model output, or customer content.

See [the implementation guide](references/implementation-guide.md) for bounded
sender and receiver patterns plus the qualification matrix.

## Output

Produce an integration record containing:

- closed trigger and callback schemas with local byte limits;
- exact trigger destination-validation rules and secret-manager references;
- distinct trigger and callback authentication boundaries;
- shared idempotency, durable queue, retry, dead-letter, and reconciliation policy;
- callback allowlist and durable acknowledgement contract;
- synthetic positive, negative-auth, malformed, duplicate, retry, and restart receipts;
- Tasks-view correlation and sanitized destination evidence; and
- final `VERIFIED`, `FAILED`, or `NOT VERIFIED` disposition with owners.

## Examples

### Minimal verified flow

```text
source event
  -> closed schema
  -> shared idempotency + durable queue
  -> exact public.lindy.ai HTTPS trigger + generated Bearer secret
  -> Lindy task correlated by requestId
  -> fixed application callback + distinct Bearer secret
  -> authenticated validation + durable enqueueOnce
  -> terminal outcome ledger
```

### Correct handling of a 2xx response

If the trigger returns 2xx but no matching task can be found, record
`ACCEPTED_UNVERIFIED`, keep the event reconcilable, and investigate. Do not mark the
business operation complete or send a blind sequence of retries.

## Error Handling

| Failure | Required response |
|---|---|
| Trigger URL fails exact sink validation | Refuse to construct the secret-bearing request |
| Generated trigger secret is empty | Fail startup or configuration validation |
| Trigger payload is malformed or excessive | Reject before claim, enqueue, or send |
| 401/403 or permanent 4xx | Stop retries, redact telemetry, alert owner |
| 408/429/selected 5xx | Apply bounded retry; dead-letter after exhaustion |
| Ambiguous timeout | Reconcile stable request ID; do not claim exactly-once delivery |
| Callback target is caller-controlled or not allowlisted | Do not attach callback secret |
| Callback auth/schema fails | Return non-2xx and create no durable job |
| Durable enqueue fails | Return non-2xx; never acknowledge unpersisted work |
| 2xx without a matching task | Mark `ACCEPTED_UNVERIFIED` and investigate |

## Resources

- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Lindy Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Lindy Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Detailed sender, receiver, and test patterns](references/implementation-guide.md)
