# Lindy Webhook Integration Guide

This guide implements application-owned safety around Lindy's documented Webhook
Received trigger and HTTP Request action. The numeric bounds are examples of local
policy, not Lindy service limits.

## Contents

1. [Trust model](#trust-model)
2. [Closed trigger contract](#closed-trigger-contract)
3. [Durable trigger pipeline](#durable-trigger-pipeline)
4. [Bounded delivery](#bounded-delivery)
5. [Authenticated callback](#authenticated-callback)
6. [Task reconciliation](#task-reconciliation)
7. [Qualification matrix](#qualification-matrix)

## Trust Model

```text
application -- generated trigger Bearer secret --> Lindy Webhook Received
Lindy HTTP Request -- distinct callback Bearer secret --> application
```

The first secret is generated in the Lindy webhook trigger. The application owns
the second secret and configures it in the outbound action. Do not reuse either
secret, infer an HMAC signature scheme, or treat request headers and callback URLs
as trusted payload data.

## Closed Trigger Contract

Define and validate the business event before it reaches a queue or HTTP client:

```typescript
type TriggerEvent = {
  requestId: string;
  eventType: 'case_opened' | 'case_updated';
  subjectId: string;
  occurredAt: string;
};

const MAX_TRIGGER_BYTES = 16 * 1024; // local example policy

function validateTriggerEvent(value: unknown): TriggerEvent {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('trigger event must be an object');
  }
  const record = value as Record<string, unknown>;
  const allowed = new Set(['requestId', 'eventType', 'subjectId', 'occurredAt']);
  if (Object.keys(record).some((key) => !allowed.has(key))) {
    throw new Error('unknown trigger field');
  }
  if (
    typeof record.requestId !== 'string' ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(record.requestId)
  ) {
    throw new Error('invalid requestId');
  }
  if (record.eventType !== 'case_opened' && record.eventType !== 'case_updated') {
    throw new Error('invalid eventType');
  }
  if (typeof record.subjectId !== 'string' || record.subjectId.length > 128) {
    throw new Error('invalid subjectId');
  }
  if (
    typeof record.occurredAt !== 'string' ||
    !Number.isFinite(Date.parse(record.occurredAt))
  ) {
    throw new Error('invalid occurredAt');
  }

  const event: TriggerEvent = {
    requestId: record.requestId,
    eventType: record.eventType,
    subjectId: record.subjectId,
    occurredAt: record.occurredAt,
  };
  if (Buffer.byteLength(JSON.stringify(event), 'utf8') > MAX_TRIGGER_BYTES) {
    throw new Error('trigger event exceeds local byte policy');
  }
  return event;
}
```

When the producer is an HTTP server, enforce the byte limit on raw input before
JSON parsing. Keep sensitive source data behind `subjectId`; let the workflow fetch
only the approved fields it actually needs through an authenticated integration.

## Durable Trigger Pipeline

Use atomic, shared infrastructure contracts:

```typescript
type TriggerJob = {
  requestId: string;
  event: TriggerEvent;
  attempt: number;
  firstAttemptAt: string;
};

interface DurableTriggerJobs {
  // Couple the idempotency claim and enqueue in one durable transaction.
  enqueueOnce(event: TriggerEvent): Promise<'created' | 'duplicate'>;
  reschedule(job: TriggerJob, delayMs: number): Promise<void>;
  deadLetter(job: TriggerJob, reason: string): Promise<void>;
}

interface TriggerOutcomes {
  record(input: {
    requestId: string;
    attempt: number;
    disposition: string;
    status?: number;
    latencyMs?: number;
  }): Promise<void>;
}
```

A module-level set or in-memory queue is insufficient for multiple processes and
does not survive termination. If claim plus enqueue cannot share a transaction,
use a recoverable lease and a sweeper for stranded claims.

## Bounded Delivery

Validate the destination before loading the secret:

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
    throw new Error('invalid Lindy webhook destination');
  }
  const secret = env.LINDY_TRIGGER_SECRET ?? '';
  if (secret.length === 0) throw new Error('missing Lindy trigger secret');
  return { url, secret };
}
```

Make one attempt and classify only the HTTP semantics the application owns:

```typescript
type Attempt =
  | { kind: 'accepted'; status: number; latencyMs: number }
  | { kind: 'permanent'; status: number; latencyMs: number }
  | { kind: 'transient'; status?: number; latencyMs: number; retryAfterMs?: number };

const REQUEST_TIMEOUT_MS = 30_000;
const MAX_RETRY_DELAY_MS = 60_000;

function retryAfter(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = Number(value);
  const requested = Number.isFinite(seconds)
    ? Math.max(0, seconds * 1000)
    : Math.max(0, Date.parse(value) - Date.now());
  return Number.isFinite(requested)
    ? Math.min(requested, MAX_RETRY_DELAY_MS)
    : undefined;
}

async function postTrigger(config: TriggerConfig, event: TriggerEvent): Promise<Attempt> {
  const started = Date.now();
  try {
    const response = await fetch(config.url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${config.secret}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    const latencyMs = Date.now() - started;
    await response.body?.cancel();

    if (response.status >= 200 && response.status < 300) {
      return { kind: 'accepted', status: response.status, latencyMs };
    }
    if ([408, 429, 500, 502, 503, 504].includes(response.status)) {
      return {
        kind: 'transient',
        status: response.status,
        latencyMs,
        retryAfterMs: retryAfter(response.headers.get('Retry-After')),
      };
    }
    return { kind: 'permanent', status: response.status, latencyMs };
  } catch {
    return { kind: 'transient', latencyMs: Date.now() - started };
  }
}
```

The worker caps attempts and total job age, applies exponential backoff with full
jitter, honors only a bounded `Retry-After`, and dead-letters after exhaustion. It
reuses `requestId` on every attempt. A timeout is ambiguous, and a 2xx result is
only `accepted_unverified` until task reconciliation succeeds.

## Authenticated Callback

Configure a pre-approved HTTPS callback URL in Lindy's HTTP Request action and set
the Authorization header to the application-owned callback secret. Dynamic
callback destinations require exact application-owned allowlisting before a secret
can be attached.

Authenticate before processing the body:

```typescript
import { timingSafeEqual } from 'node:crypto';

const callbackSecret = process.env.LINDY_CALLBACK_SECRET ?? '';
if (callbackSecret.length === 0) throw new Error('missing callback secret');

function callbackAuthorized(header: string | undefined): boolean {
  if (!header?.startsWith('Bearer ')) return false;
  const actual = Buffer.from(header.slice('Bearer '.length));
  const expected = Buffer.from(callbackSecret);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

type Callback = {
  requestId: string;
  taskId: string;
  status: 'completed' | 'failed';
};

function validateCallback(value: unknown): Callback {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('callback must be an object');
  }
  const record = value as Record<string, unknown>;
  const allowed = new Set(['requestId', 'taskId', 'status']);
  if (Object.keys(record).some((key) => !allowed.has(key))) {
    throw new Error('unknown callback field');
  }
  if (typeof record.requestId !== 'string' || record.requestId.length > 128) {
    throw new Error('invalid requestId');
  }
  if (typeof record.taskId !== 'string' || record.taskId.length > 128) {
    throw new Error('invalid taskId');
  }
  if (record.status !== 'completed' && record.status !== 'failed') {
    throw new Error('invalid status');
  }
  return {
    requestId: record.requestId,
    taskId: record.taskId,
    status: record.status,
  };
}
```

Use an application-owned raw request-byte limit before parsing. Then couple schema
validation to a durable, atomic receiver contract:

```typescript
interface DurableCallbacks {
  enqueueOnce(requestId: string, callback: Callback): Promise<'created' | 'duplicate'>;
}

const MAX_CALLBACK_BYTES = 16 * 1024; // local example policy

async function acceptCallback(
  authorization: string | undefined,
  rawBody: Uint8Array,
  callbacks: DurableCallbacks,
): Promise<{ status: number; disposition: string }> {
  if (!callbackAuthorized(authorization)) {
    return { status: 401, disposition: 'unauthorized' };
  }
  if (rawBody.byteLength > MAX_CALLBACK_BYTES) {
    return { status: 413, disposition: 'oversized' };
  }

  let callback: Callback;
  try {
    callback = validateCallback(JSON.parse(new TextDecoder().decode(rawBody)));
  } catch {
    return { status: 400, disposition: 'invalid' };
  }

  const disposition = await callbacks.enqueueOnce(callback.requestId, callback);
  return { status: 202, disposition };
}
```

If persistence fails, propagate a non-2xx result. Never acknowledge and then rely
on an unawaited promise, timer, or process-local queue.

## Task Reconciliation

Maintain explicit states:

```text
queued -> attempted -> accepted_unverified -> completed | failed | unknown
                   \-> permanent_failure
                   \-> retry_scheduled -> dead_letter
```

Correlate the stable request ID to the Lindy Tasks view or the authenticated
callback. Record only request ID, task ID, status, timestamps, and sanitized
operational metadata. Alert when `accepted_unverified` exceeds the local deadline.

Do not claim exactly-once remote execution. An ambiguous timeout can result in a
created task even if the caller never receives its response.

## Qualification Matrix

| Test | Expected response | Durable jobs | Lindy task / side effect |
|---|---:|---:|---:|
| Valid trigger | 2xx acceptance | one source job | one correlated task |
| Wrong trigger secret | non-2xx | source job terminal/review | no task |
| Lookalike or HTTP trigger URL | no request | none sent | no task |
| Malformed or oversized trigger | local rejection | zero | no task |
| Concurrent duplicate trigger | one local job | one | reconcile at most one intended operation |
| Transient response | bounded retries | one logical job | reconciled or dead-lettered |
| Valid callback | 2xx after persistence | one callback job | one intended side effect |
| Wrong callback secret | 401/403 | zero | no side effect |
| Malformed or oversized callback | 4xx | zero | no side effect |
| Duplicate callback | duplicate disposition | one total | at most one side effect |
| Durable store unavailable | non-2xx | zero or safely pending | no acknowledged loss |
| Worker termination | queue recovers | job remains durable | outcome reconciled |

Inspect logs after every test: no secret, full webhook URL, headers, payload,
prompt, model output, or customer data may appear.

## Official References

- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Lindy Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Lindy Test Panel](https://docs.lindy.ai/testing/test-panel)
