# Lindy Production Readiness Evidence Guide

Use this guide to turn the production checklist into a reproducible decision.
The Lindy workspace, current contract, deployed application, and retained test
evidence remain authoritative.

## Contents

1. [Evidence record](#evidence-record)
2. [Authentication boundaries](#authentication-boundaries)
3. [Callback receiver contract](#callback-receiver-contract)
4. [Durable enqueue qualification](#durable-enqueue-qualification)
5. [Task-level proof](#task-level-proof)
6. [Test matrix](#test-matrix)

## Evidence Record

Create one record per release and target workspace:

```markdown
# Lindy production readiness: <release>

Workspace: <workspace identifier>
Agent: <agent identifier>
Release owner: <name or team>
Reviewer: <name or team>
Reviewed at: <timestamp>

| Check | Verdict | Evidence | Owner / follow-up |
|---|---|---|---|
| Trigger URL and generated secret | PASS / FAIL / NOT VERIFIED | <redacted link> | <owner> |
| Synthetic task creation | PASS / FAIL / NOT VERIFIED | <task ID and correlation ID> | <owner> |
| Callback authentication | PASS / FAIL / NOT VERIFIED | <test run> | <owner> |
| Durable enqueue | PASS / FAIL / NOT VERIFIED | <restart test> | <owner> |
| Duplicate suppression | PASS / FAIL / NOT VERIFIED | <concurrency test> | <owner> |
| Disable or rollback | PASS / FAIL / NOT VERIFIED | <runbook exercise> | <owner> |
| Contract-dependent requirements | PASS / FAIL / NOT VERIFIED / N/A | <current source> | <owner> |

Decision: GO / NO-GO
Approver: <accountable owner>
```

Store references to evidence, not secrets, full payloads, or copied customer data.

## Authentication Boundaries

There are two independent directions:

```text
application -- Lindy-generated trigger secret --> Lindy webhook trigger
Lindy HTTP Request action -- application-owned callback secret --> application
```

The application must send the trigger secret only to an HTTPS URL whose hostname
is exactly `public.lindy.ai`. The callback receiver must use a different secret,
chosen and stored by the application operator. Configure it as an Authorization
header on the Lindy HTTP Request action.

Do not infer that a successful trigger request authenticates a later callback.
Test both boundaries independently, including their rejection paths.

## Callback Receiver Contract

Mount authentication before a JSON body parser whenever the framework permits.
At minimum, do not inspect, log, enqueue, or act on the body until authorization
succeeds. Validate the secret at startup and compare bearer values in constant time.

```typescript
import { timingSafeEqual } from 'node:crypto';

const callbackSecret = process.env.LINDY_CALLBACK_SECRET ?? '';
if (callbackSecret.length === 0) {
  throw new Error('LINDY_CALLBACK_SECRET is required');
}

function authorized(header: string | undefined): boolean {
  const prefix = 'Bearer ';
  if (!header?.startsWith(prefix)) return false;
  const actual = Buffer.from(header.slice(prefix.length));
  const expected = Buffer.from(callbackSecret);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
```

Define a closed payload schema. The values below illustrate an application-owned
contract, not a Lindy platform schema:

```typescript
type Callback = {
  requestId: string;
  status: 'completed' | 'failed';
  taskId: string;
};

function parseCallback(value: unknown): Callback {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('callback must be an object');
  }
  const record = value as Record<string, unknown>;
  const allowed = new Set(['requestId', 'status', 'taskId']);
  if (Object.keys(record).some((key) => !allowed.has(key))) {
    throw new Error('unknown callback field');
  }
  if (typeof record.requestId !== 'string' || record.requestId.length > 128) {
    throw new Error('invalid requestId');
  }
  if (record.status !== 'completed' && record.status !== 'failed') {
    throw new Error('invalid status');
  }
  if (typeof record.taskId !== 'string' || record.taskId.length > 128) {
    throw new Error('invalid taskId');
  }
  return record as Callback;
}
```

Apply an explicit request-byte limit in the HTTP server before parsing. Choose the
limit from the documented callback contract; do not represent it as a Lindy limit.

## Durable Enqueue Qualification

The handler may return success only after its durable queue confirms persistence:

```typescript
interface DurableQueue {
  enqueueOnce(key: string, payload: Callback): Promise<'created' | 'duplicate'>;
}

async function acceptCallback(
  authorization: string | undefined,
  body: unknown,
  queue: DurableQueue,
): Promise<{ status: number; result: string }> {
  if (!authorized(authorization)) return { status: 401, result: 'unauthorized' };

  let callback: Callback;
  try {
    callback = parseCallback(body);
  } catch {
    return { status: 400, result: 'invalid payload' };
  }

  const disposition = await queue.enqueueOnce(callback.requestId, callback);
  return { status: 202, result: disposition };
}
```

`enqueueOnce` must be atomic and survive process or host termination. An array,
timer, background promise, framework-local task, or process-local queue does not
qualify. If the queue write fails or times out, return a non-2xx response so the
request is not falsely acknowledged.

## Task-Level Proof

For each synthetic trigger test:

1. Generate a unique correlation ID.
2. Send the approved bounded payload to the validated trigger URL.
3. Record the response status without recording the secret or full response.
4. Find the corresponding task in Lindy's Tasks view.
5. Verify the intended agent and expected terminal state.
6. Record only the correlation ID, task ID, timestamps, and verdict.

A 2xx response without steps 4-5 is `NOT VERIFIED`. A deliberately unauthorized
request passes its negative test only if the response is non-2xx and no task was
created.

## Test Matrix

| Scenario | Expected HTTP outcome | Expected durable jobs | Expected Lindy task |
|---|---:|---:|---:|
| Valid trigger | 2xx transport acceptance | N/A | exactly one matching task |
| Wrong trigger secret | non-2xx | N/A | none |
| Valid callback | 2xx after enqueue | one | existing task correlated |
| Wrong callback secret | 401/403 | zero | unchanged |
| Unknown callback field | 4xx | zero | unchanged |
| Oversized callback | 4xx | zero | unchanged |
| Same callback twice | 2xx/duplicate disposition | one total | unchanged |
| Worker dies after enqueue | already acknowledged | job remains recoverable | unchanged |
| Durable store unavailable | non-2xx | zero or safely pending | unchanged |

Retain the run receipt, sanitized logs, queue evidence, and task identifiers with
the readiness decision.

## Official References

- [Lindy webhook triggers](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request actions](https://docs.lindy.ai/skills/by-lindy/http-request)
