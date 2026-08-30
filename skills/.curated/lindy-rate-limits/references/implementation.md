# Lindy Webhook Worker -- Secure Reference Pattern

This TypeScript pattern demonstrates application-owned validation, idempotency,
shared admission control, and bounded delivery to a documented Lindy webhook
trigger. Adapt interfaces to production infrastructure and test them under
contention and failure. Numeric bounds below are local example policy, not Lindy
service limits.

## Configuration Boundary

Validate the destination before loading or using the trigger secret:

```typescript
type TriggerConfig = {
  url: URL;
  secret: string;
};

function loadTriggerConfig(env: NodeJS.ProcessEnv): TriggerConfig {
  const url = new URL(env.LINDY_TRIGGER_URL ?? '');
  if (
    url.protocol !== 'https:' ||
    url.hostname !== 'public.lindy.ai' ||
    url.username !== '' ||
    url.password !== '' ||
    !url.pathname.startsWith('/api/v1/webhooks/')
  ) {
    throw new Error('LINDY_TRIGGER_URL is not an approved Lindy webhook URL');
  }

  const secret = env.LINDY_TRIGGER_SECRET ?? '';
  if (secret.length === 0) throw new Error('LINDY_TRIGGER_SECRET is required');
  return { url, secret };
}
```

Keep `LINDY_CALLBACK_SECRET` separate. It authenticates calls in the opposite
direction and must never be passed to `loadTriggerConfig`.

## Closed Event Schema

This is an application-owned example contract:

```typescript
type TriggerEvent = {
  requestId: string;
  kind: 'customer_created' | 'ticket_updated';
  subjectId: string;
  occurredAt: string;
};

const MAX_PAYLOAD_BYTES = 16 * 1024; // local example policy; tune and document it

function validateEvent(value: unknown): TriggerEvent {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('event must be an object');
  }
  const record = value as Record<string, unknown>;
  const allowed = new Set(['requestId', 'kind', 'subjectId', 'occurredAt']);
  if (Object.keys(record).some((key) => !allowed.has(key))) {
    throw new Error('event contains an unknown field');
  }
  if (
    typeof record.requestId !== 'string' ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(record.requestId)
  ) {
    throw new Error('invalid requestId');
  }
  if (record.kind !== 'customer_created' && record.kind !== 'ticket_updated') {
    throw new Error('invalid kind');
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

  const event = record as TriggerEvent;
  if (Buffer.byteLength(JSON.stringify(event), 'utf8') > MAX_PAYLOAD_BYTES) {
    throw new Error('event exceeds local payload policy');
  }
  return event;
}
```

Enforce an HTTP request-byte limit before parsing if these events arrive through
an inbound server. Never log the full event by default.

## Durable Admission Interfaces

The implementations behind these interfaces must be shared and atomic:

```typescript
type TriggerJob = {
  requestId: string;
  event: TriggerEvent;
  attempt: number;
  firstAttemptAt: string;
};

interface DurableJobs {
  // Couple the idempotency claim and durable enqueue in one transaction.
  enqueueOnce(event: TriggerEvent): Promise<'created' | 'duplicate'>;
  reschedule(job: TriggerJob, delayMs: number): Promise<void>;
  deadLetter(job: TriggerJob, reason: string): Promise<void>;
}

interface SharedAdmissionControl {
  // The implementation performs one atomic mutation in a shared store.
  acquire(key: string): Promise<{ admitted: boolean; retryAfterMs: number }>;
}

interface OutcomeLedger {
  record(input: {
    requestId: string;
    attempt: number;
    disposition: string;
    httpStatus?: number;
    latencyMs?: number;
  }): Promise<void>;
}
```

Do not implement these contracts with module-level maps or arrays in a scaled
deployment. If the idempotency claim and enqueue cannot share a transaction, use
a recoverable lease plus a sweeper for stranded reservations.

## One Bounded Attempt

```typescript
type AttemptResult =
  | { kind: 'accepted'; status: number; latencyMs: number }
  | { kind: 'permanent'; status: number; latencyMs: number }
  | { kind: 'transient'; status?: number; retryAfterMs?: number; latencyMs: number };

const REQUEST_TIMEOUT_MS = 30_000; // local example policy
const MAX_RETRY_DELAY_MS = 60_000; // local example policy

function boundedRetryAfter(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = Number(value);
  const requestedMs = Number.isFinite(seconds)
    ? Math.max(0, seconds * 1000)
    : Math.max(0, Date.parse(value) - Date.now());
  return Number.isFinite(requestedMs)
    ? Math.min(requestedMs, MAX_RETRY_DELAY_MS)
    : undefined;
}

async function postOnce(config: TriggerConfig, event: TriggerEvent): Promise<AttemptResult> {
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
    if (response.status === 408 || response.status === 429 || response.status >= 500) {
      return {
        kind: 'transient',
        status: response.status,
        retryAfterMs: boundedRetryAfter(response.headers.get('Retry-After')),
        latencyMs,
      };
    }
    return { kind: 'permanent', status: response.status, latencyMs };
  } catch {
    // A timeout is ambiguous: the remote service may have accepted the request.
    return { kind: 'transient', latencyMs: Date.now() - started };
  }
}
```

Do not treat the body as a stable API contract. A 2xx result remains accepted but
unverified until a matching task or authenticated callback is observed.

## Bounded Worker

```typescript
const MAX_ATTEMPTS = 4; // local example policy
const BASE_DELAY_MS = 1_000;

function fullJitter(attempt: number): number {
  const cap = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_RETRY_DELAY_MS);
  return Math.floor(Math.random() * cap);
}

async function runTriggerJob(
  job: TriggerJob,
  agentKey: string,
  config: TriggerConfig,
  jobs: DurableJobs,
  limiter: SharedAdmissionControl,
  ledger: OutcomeLedger,
): Promise<void> {
  if (!/^[A-Za-z0-9._:-]{1,128}$/.test(agentKey)) {
    throw new Error('invalid internal agent key');
  }
  const admission = await limiter.acquire(`agent:${agentKey}`);
  if (!admission.admitted) {
    await jobs.reschedule(job, Math.min(admission.retryAfterMs, MAX_RETRY_DELAY_MS));
    return;
  }

  const result = await postOnce(config, job.event);
  await ledger.record({
    requestId: job.requestId,
    attempt: job.attempt,
    disposition: result.kind,
    httpStatus: result.status,
    latencyMs: result.latencyMs,
  });

  if (result.kind === 'accepted') return;
  if (result.kind === 'permanent') {
    await jobs.deadLetter(job, `permanent HTTP ${result.status}`);
    return;
  }
  if (job.attempt + 1 >= MAX_ATTEMPTS) {
    await jobs.deadLetter(job, 'transient attempts exhausted');
    return;
  }

  const delay = result.retryAfterMs ?? fullJitter(job.attempt);
  await jobs.reschedule({ ...job, attempt: job.attempt + 1 }, delay);
}
```

Map the generated webhook path to a sanitized internal `agentKey`; do not place
the full path in telemetry or shared-store keys. The worker must also apply a
total job-age deadline so repeated queue deferrals cannot continue indefinitely.

## Completion Reconciliation

Maintain these distinct states:

```text
queued -> admitted -> accepted_unverified -> completed | failed | unknown
                       \-> permanent_failure
                       \-> retry_scheduled -> dead_letter
```

Move `accepted_unverified` to a terminal task state only after correlating the
stable request ID with Lindy's Tasks view or an authenticated callback. Alert on
records that remain unverified beyond the local reconciliation deadline.

## Security and Failure Tests

1. Supply a lookalike host, an HTTP URL, embedded credentials, and an unexpected
   path; configuration must fail before an Authorization header is constructed.
2. Start without `LINDY_TRIGGER_SECRET`; startup must fail.
3. Race the same request ID through multiple producers; `enqueueOnce` creates one
   job.
4. Race multiple workers at the shared policy boundary; aggregate admissions stay
   within the local policy.
5. Inject 401, 429, 503, timeout, and malformed input outcomes; verify the exact
   permanent, bounded-retry, ambiguous, and rejection dispositions.
6. Terminate a worker after dequeue and after remote acceptance; verify queue
   recovery and reconciliation without claiming exactly-once remote execution.
7. Inspect logs and alerts for secrets, generated URLs, and full payloads.

## Official References

- [Lindy webhook triggers](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request actions](https://docs.lindy.ai/skills/by-lindy/http-request)
