---
name: lindy-prod-checklist
description: 'Production readiness checklist for Lindy AI agent deployments.

  Use when preparing agents for production, auditing live agents,

  or validating go-live readiness.

  Trigger with phrases like "lindy production", "lindy prod ready",

  "lindy go live", "lindy deployment checklist".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.20.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- deployment
- audit
compatibility: Compatible with AI coding agents that can read Markdown; optional verification probes require a shell with curl
---
# Lindy Production Checklist

## Overview

Create an evidence-backed go/no-go decision for a Lindy agent. Treat the Lindy
dashboard and the organization's current contract, workspace configuration, and
runbooks as the authorities. Do not infer product entitlements, prices, quotas,
security features, support terms, or compliance commitments from this skill.

Use **Read** to inspect configuration and evidence, **Write** or **Edit** to
maintain the readiness record, and `Bash(curl:*)` only for an approved synthetic
webhook probe. Never place a secret in the record or command output.

## Prerequisites

- Access to the target Lindy workspace and its **Tasks** view.
- An exported webhook-trigger URL and its nonempty Lindy-generated trigger secret.
- A separate, nonempty callback secret when a Lindy HTTP Request action calls your
  application. Never reuse the trigger secret as the callback secret.
- A synthetic test case with no production personal or confidential data and a
  unique correlation ID.
- Access to current contract/workspace evidence for any claim about pricing,
  credits, thresholds, secret rotation, SSO, SCIM, support, or a BAA.
- A durable queue when callback work cannot be completed safely within the
  receiver's synchronous response window.

## Instructions

### 1. Open an evidence record

Record the workspace, agent, reviewer, date, release identifier, and links to
artifacts. Give every check one of three verdicts: `PASS`, `FAIL`, or
`NOT VERIFIED`. A missing entitlement or policy document is `NOT VERIFIED`, not
an assumed pass.

### 2. Verify the two authentication boundaries

For an application calling a Lindy webhook trigger:

- Confirm the URL uses HTTPS and its hostname is exactly `public.lindy.ai`.
- Confirm the authorization value is the secret generated for that trigger.
- Keep the URL and trigger secret in an approved secret manager; redact both from
  screenshots, logs, tickets, and readiness reports.

For a Lindy HTTP Request action calling your application:

- Generate and store an independent `LINDY_CALLBACK_SECRET` in your application.
- Configure the action to send `Authorization: Bearer <callback-secret>`.
- Reject a missing or mismatched value before accepting or acting on the body.
- Apply a bounded schema and payload-size limit before enqueueing work.

Lindy documents the trigger-side generated secret and configurable headers for
HTTP Request actions. It does not make one secret interchangeable across both
directions.

### 3. Prove a real synthetic task is created

Run a probe only after the URL and secret checks pass:

```bash
set -euo pipefail

: "${LINDY_TRIGGER_URL:?LINDY_TRIGGER_URL is required}"
: "${LINDY_TRIGGER_SECRET:?LINDY_TRIGGER_SECRET is required}"

case "$LINDY_TRIGGER_URL" in
  https://public.lindy.ai/api/v1/webhooks/*) ;;
  *) echo "Refusing to send the trigger secret to a non-Lindy host" >&2; exit 1 ;;
esac

CORRELATION_ID="prod-readiness-REPLACE_WITH_UNIQUE_ID"
HTTP_STATUS=$(curl --silent --show-error --output /dev/null \
  --write-out '%{http_code}' --max-time 30 \
  --request POST "$LINDY_TRIGGER_URL" \
  --header "Authorization: Bearer $LINDY_TRIGGER_SECRET" \
  --header 'Content-Type: application/json' \
  --data "{\"correlationId\":\"$CORRELATION_ID\",\"kind\":\"readiness_probe\"}")

case "$HTTP_STATUS" in
  2??) echo "Transport accepted; verify the task separately: $CORRELATION_ID" ;;
  *) echo "Trigger rejected with HTTP $HTTP_STATUS" >&2; exit 1 ;;
esac
```

The 2xx response proves only transport acceptance. Find a task with the unique
correlation ID in Lindy's Tasks view, then verify its expected actions and final
state. If authentication is intentionally broken, require a non-2xx response and
also verify that no task was created. Do not capture the response body in the
evidence record.

### 4. Qualify callback durability

A callback receiver passes only if it authenticates first, validates a bounded
schema, and persists accepted work to a durable queue before returning success.
An in-memory promise, timer, or process-local queue is not durable enqueue. Test:

1. valid callback -> one durable job and a 2xx response;
2. wrong or missing callback secret -> non-2xx and no job;
3. malformed or oversized payload -> non-2xx and no job;
4. duplicate correlation ID -> no duplicate side effect; and
5. worker interruption after enqueue -> the job remains recoverable.

### 5. Complete the operational gate

- Exercise the happy path and each material failure path with synthetic data.
- Confirm OAuth integrations and target resources using the workspace UI.
- Establish an observed latency and task-success baseline; choose alert thresholds
  from the organization's risk appetite and actual workload.
- Link the incident runbook, owner, escalation path, rollback or disable procedure,
  data-retention decision, and monitoring evidence.
- Verify pricing, credit budget, secret-rotation cadence, SSO, SCIM, BAA, and other
  compliance statements only from current contract or workspace evidence. Mark
  unavailable or inapplicable features explicitly.

### 6. Make the decision

Block launch for any failed authentication boundary, unverified task creation,
unauthenticated callback, nondurable accepted work, missing rollback path, or
unresolved high-severity finding. The accountable owner must accept any remaining
lower-severity risk in the evidence record.

## Output

Produce a readiness record containing:

- release, workspace, agent, owner, reviewer, and review timestamp;
- per-check `PASS` / `FAIL` / `NOT VERIFIED` verdicts with evidence links;
- synthetic correlation IDs and task identifiers, without payloads or secrets;
- callback rejection, deduplication, and durable-enqueue test results;
- contract-dependent claims with their current source and applicability;
- unresolved risks, accountable owners, and due dates; and
- a final `GO` or `NO-GO` decision with the approving owner.

## Examples

### Minimal go/no-go summary

```markdown
# Release r42 readiness

- Trigger auth: PASS -- synthetic task task-123 matched correlation prod-readiness-42
- Callback auth: PASS -- wrong secret rejected; zero jobs created
- Durable enqueue: PASS -- job survived worker restart and completed once
- SSO/SCIM: NOT VERIFIED -- not required for this release; contract owner recorded
- Rollback: PASS -- agent disable procedure tested by operator
- Open risks: none above accepted severity

Decision: GO
Approver: release owner
```

### Correct no-go outcome

If the webhook returns 2xx but no corresponding task appears, record
`Task creation: NOT VERIFIED` and choose `NO-GO`. Do not substitute a public-host
reachability check for task-level proof.

## Error Handling

| Failure | Required response |
|---|---|
| Trigger URL is not HTTPS on exact `public.lindy.ai` host | Do not attach the trigger secret; block the probe |
| Missing or reused secret | Generate distinct secrets, store them correctly, and repeat the tests |
| 2xx without a matching task | Treat as unverified; inspect the Tasks view and agent trigger configuration |
| Rejected request creates a task | Block launch and escalate the authentication failure |
| Callback acknowledges before durable enqueue | Change the receiver contract and repeat interruption testing |
| Contract-dependent feature cannot be proven | Mark `NOT VERIFIED`; do not advertise or depend on it |

## Resources

- [Lindy webhook trigger documentation](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request action documentation](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Detailed evidence and receiver patterns](references/implementation-guide.md)
