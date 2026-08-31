# Lindy Trigger Traffic-Control Guide

This guide defines the evidence and architecture needed to control outbound
traffic to Lindy webhook triggers. It deliberately contains no fixed Lindy price,
credit, request-rate, concurrency, or action-limit values.

## Contents

1. [Evidence inventory](#evidence-inventory)
2. [Trust boundaries](#trust-boundaries)
3. [Admission architecture](#admission-architecture)
4. [Idempotency limits](#idempotency-limits)
5. [Response policy](#response-policy)
6. [Observability](#observability)
7. [Qualification tests](#qualification-tests)

## Evidence Inventory

Before choosing controls, record:

| Fact | Authoritative source | Reviewed at | Owner |
|---|---|---|---|
| Workspace usage and available credits | target workspace UI | timestamp | FinOps owner |
| Contract-specific constraints | current order form or contract | timestamp | contract owner |
| Observed task throughput and latency | retained task/run evidence | window | service owner |
| Application traffic envelope | application telemetry | window | service owner |
| Local retry and queue policy | approved design record | revision | engineering owner |

If a source does not state a platform constraint, mark it unknown. Never fill the
gap with an old blog post, copied skill, guessed default, or hard-coded table.

## Trust Boundaries

Validate the webhook destination before constructing an Authorization header:

- scheme is `https`;
- hostname is exactly `public.lindy.ai`;
- URL has no embedded username or password;
- path is the generated webhook path expected by the application; and
- the per-trigger secret is nonempty and loaded from an approved secret manager.

The caller's trigger secret authenticates to Lindy. An application callback
receiver needs a separate application-owned callback secret. Rotation, expiry,
and overlap procedures are organization choices unless current authoritative
evidence says otherwise.

## Admission Architecture

Use shared, durable components whenever multiple senders exist:

```text
producer
  -> closed schema and byte-bound validation
  -> atomic idempotency reservation
  -> durable queue / transactional outbox
  -> shared atomic admission control
  -> webhook worker
  -> durable outcome ledger and reconciliation
```

The admission controller can use a token bucket, leaky bucket, fixed concurrency
semaphore, or a combination. Its state must be shared and mutations atomic.
Choose keys that preserve intended isolation, such as `tenant + agent`, and add a
global ceiling only when the deployment needs one.

Do not silently fall back to a process-local limiter when the shared store fails.
Keep work durable or shed it explicitly according to the approved policy.

## Idempotency Limits

Require a stable request ID derived from the source business event. Atomically
associate it with the durable job. Prefer a transactional outbox or a queue that
supports unique job keys. If reservation and enqueue cannot be one transaction,
use a lease and a recovery process so a crash cannot strand a permanent claim.

Local idempotency prevents duplicate local jobs. It cannot guarantee exactly-once
execution across an ambiguous network timeout: Lindy may have accepted a request
even when the caller did not receive the response. Keep the same request ID on
every attempt, reconcile it against the Tasks view or authenticated callback, and
design downstream actions to tolerate duplicates where possible.

Do not assume Lindy honors an `Idempotency-Key` request header unless the current
official webhook documentation explicitly states that behavior.

## Response Policy

Classify outcomes explicitly:

| Outcome | Disposition |
|---|---|
| 2xx | transport accepted; await task corroboration |
| 408 | transient candidate; bounded retry |
| 429 | transient candidate; honor bounded `Retry-After` when valid |
| selected 5xx | transient candidate; bounded retry |
| 401/403 | permanent authentication failure; stop and alert |
| other 4xx | permanent request failure unless current documentation proves otherwise |
| timeout / connection reset | ambiguous; reconcile before or during bounded retry |

Cap attempt count, per-attempt timeout, backoff delay, and total elapsed time.
After exhaustion, write a terminal outcome, move the event to a dead-letter queue,
and alert the accountable owner. A recursive retry with no limit is prohibited.

## Observability

Record only identifiers and operational metadata:

- request ID, queue job ID, and sanitized agent identifier;
- admission outcome and shared-limiter key;
- attempt number, latency, and response status class;
- retry schedule and terminal disposition;
- task ID once corroborated; and
- queue age, depth, dead-letter count, and duplicate count.

Never log Authorization headers, webhook URLs containing sensitive identifiers,
full request/response bodies, customer content, or secrets.

## Qualification Tests

| Test | Passing evidence |
|---|---|
| Exact-host rejection | secret is never sent to lookalike, HTTP, credential-bearing, or unexpected URLs |
| Empty secret | configuration fails before a request is possible |
| Schema and size bounds | unknown, malformed, and oversized events create no durable job |
| Concurrent duplicate | two instances produce one durable job for one request ID |
| Shared limit contention | combined traffic from all instances respects the chosen local policy |
| Store outage | no silent per-process fallback; work remains durable or is explicitly rejected |
| Transient response | bounded retries use jitter and reach a terminal disposition |
| Permanent 4xx | no retry storm; owner receives a redacted alert |
| Worker termination | queued work survives and resumes according to policy |
| Ambiguous timeout | request is reconciled using the stable request ID |
| 2xx response | matching task is found before completion is claimed |

Retain sanitized test receipts and review the design whenever traffic, topology,
contract, or workspace configuration changes.

## Official References

- [Lindy webhook triggers](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request actions](https://docs.lindy.ai/skills/by-lindy/http-request)
