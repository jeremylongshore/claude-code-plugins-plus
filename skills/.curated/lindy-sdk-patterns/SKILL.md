---
name: lindy-sdk-patterns
description: 'Lindy integration patterns for webhook handling, HTTP actions, and
  Run Code.

  Use when building integrations, calling Lindy agents from code,

  or implementing the Run Code action with Python/JavaScript.

  Trigger with phrases like "lindy integration patterns", "lindy best practices",

  "lindy webhook patterns", "lindy Run Code", "lindy HTTP Request".

  '
allowed-tools: Read, Write, Edit
version: 1.20.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- api
compatibility: Designed for Claude Code
---
# Lindy Integration Patterns

## Overview

Use Lindy's documented integration primitives: **Webhook Received** for inbound
calls, **HTTP Request** for outbound calls, **Run Code** for bounded transformations,
and **Send POST Request to Callback** for the documented callback workflow. This is
not an SDK guide: Lindy's current public documentation does not provide the package,
client, agent CRUD, streaming, API key, or general API-host surface that older copies
of this skill claimed.

## Prerequisites

- Lindy workspace with an editable custom agent
- An application-owned HTTPS endpoint when outbound calls or callbacks are required
- A secret manager for the Lindy-generated Webhook Received secret and any separate
  credential owned by the target application
- Sanitized test fixtures and access to Tasks/Test Panel

## Authentication and Trust Boundaries

- **Inbound to Lindy:** create the webhook in the Webhook Received trigger, select
  **Generate Secret**, store the one-time value, and send it as an Authorization
  bearer value. Use only the generated `public.lindy.ai` webhook URL.
- **Outbound from Lindy:** configure authentication required by the target service in
  the HTTP Request action. This is the target service's credential, not a Lindy API
  key.
- **Callback:** Lindy's webhook guide documents `callbackUrl` and Send POST Request to
  Callback, but does not document a Lindy callback signature. Treat callback content
  as untrusted unless the receiving application establishes its own authenticated
  boundary; never invent or claim a Lindy signing header.
- Keep inbound, outbound, and callback credentials distinct. Never put secrets in a
  prompt, body, query string, task title, log, or Run Code `text` output.

## Instructions

### 1. Configure an Inbound Webhook Received Trigger

1. Add **Webhook Received** and create a named webhook.
2. Generate its secret and store it immediately; Lindy documents that it is shown
   once.
3. Choose follow-up behavior deliberately: same task, new task, or ignore.
4. Define a minimal request schema and reject oversized/unknown fields in the calling
   application before sending.
5. Send a sanitized fixture, then verify the new task in Tasks.

This is a small application wrapper around the documented webhook, not a Lindy SDK:

```typescript
type Intake = { event: 'document.ready'; documentRef: string };

async function triggerLindyWebhook(input: {
  webhookUrl: string;
  webhookSecret: string;
  payload: Intake;
}): Promise<number> {
  const url = new URL(input.webhookUrl);
  if (
    url.protocol !== 'https:' ||
    url.hostname !== 'public.lindy.ai' ||
    !url.pathname.startsWith('/api/v1/webhooks/') ||
    url.username ||
    url.password
  ) {
    throw new Error('Refusing an unrecognized Lindy webhook URL');
  }
  if (!input.webhookSecret.trim()) throw new Error('Webhook secret is empty');
  if (!/^doc_[a-z0-9_-]{1,64}$/i.test(input.payload.documentRef)) {
    throw new Error('Invalid document reference');
  }

  const response = await fetch(url, {
    method: 'POST',
    redirect: 'error',
    headers: {
      Authorization: `Bearer ${input.webhookSecret}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input.payload),
  });
  if (!response.ok) throw new Error(`Webhook rejected with status ${response.status}`);
  return response.status;
}
```

Do not blindly retry an ambiguous response: the public webhook documentation does not
promise an idempotency key. Check Tasks and the application's operation record before
a controlled retry.

### 2. Configure an Outbound HTTP Request

1. Add **HTTP Request** from Popular or By Lindy.
2. Use a fixed, allowlisted HTTPS URL rather than task-controlled host text.
3. Select the method and content type required by the target service.
4. Put the target service's protected credential in the appropriate header.
5. Constrain the body to named fields from previous steps; omit full source messages,
   headers, credentials, and unrelated context.
6. Branch on the documented status-code/response outputs and fail closed on rejected
   or malformed responses.

### 3. Use Run Code for Bounded Transformation

Lindy documents Python/JavaScript variables as strings and exposes `result`, `text`,
and `stderr` to later steps. Parse, validate, bound, and return only the minimum data:

```python
import json

data = json.loads(raw_items)
if not isinstance(data, list) or len(data) > 100:
    raise ValueError("raw_items must be a list with at most 100 entries")

allowed = []
for item in data:
    if not isinstance(item, dict) or set(item) != {"reference", "score"}:
        raise ValueError("unexpected item schema")
    reference = item["reference"]
    score = item["score"]
    if not isinstance(reference, str) or len(reference) > 64:
        raise ValueError("invalid reference")
    if not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError("invalid score")
    if score >= 0.5:
        allowed.append({"reference": reference, "score": score})

return {"count": len(allowed), "items": allowed}
```

Avoid printing input data: printed content becomes `text`. Prefer HTTP Request for
network calls so URL, authentication, response status, and error branches remain
visible in the workflow. Do not rely on an undocumented runtime, sandbox vendor,
startup time, timeout value, or library version; check the current Run Code page.

### 4. Add an Optional Callback Flow

Include a fixed application-owned `callbackUrl` only when two-way processing is
needed, then add **Send POST Request to Callback** as documented. The receiver should
accept a minimal result schema and stage the result for validation/approval. A
callback alone must not authorize payments, deletion, access changes, or external
communications.

### 5. Test the Boundaries

Verify one valid call and negative cases for a missing/wrong bearer secret, wrong
host, extra/oversized input, outbound 4xx/5xx response, malformed Run Code input, and
untrusted callback content. The Test Panel executes real actions, so use synthetic
data, test integrations, and confirmation for side effects.

## Error Handling

| Failure | Fail-closed response |
|---|---|
| Webhook returns 401 | Stop; confirm the Lindy-generated secret without printing it |
| Webhook outcome is ambiguous | Inspect Tasks/operation record before a manual retry |
| Outbound URL is dynamic or non-HTTPS | Refuse and replace it with an allowlisted endpoint |
| HTTP response is rejected or malformed | Route to an error branch; do not consume partial data |
| Run Code input violates schema | Raise an error and inspect only metadata in Tasks |
| Callback is unauthenticated/untrusted | Quarantine for validation; perform no side effect |

## Output

Return an integration contract containing:

- selected primitive and direction of trust;
- exact minimal request/response schemas and size/cardinality bounds;
- URL ownership/allowlist and distinct credential owners;
- failure, retry, callback, and human-approval behavior;
- data-minimization and logging rules; and
- a test receipt covering happy path and every negative boundary above.

## Examples

For a document workflow, the application sends only
`{"event":"document.ready","documentRef":"doc_sample_001"}` to the exact generated
webhook URL with its generated bearer secret. Lindy transforms the reference, calls a
fixed application endpoint with that endpoint's separate credential, and returns a
minimal status callback. Raw document text, user identity, and either secret never
enter the payload, prompt, task title, Run Code output, or logs.

## Resources

- [Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Run Code](https://docs.lindy.ai/skills/by-lindy/run-code)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)

## Next Steps

Use `lindy-security-basics` to review the resulting credential, connection, approval,
data, and monitoring boundaries before activating the workflow.
