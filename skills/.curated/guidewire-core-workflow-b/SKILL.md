---
name: guidewire-core-workflow-b
description: Automate the ClaimCenter FNOL→investigation→reserve→payment→settlement→close pipeline including the failure paths — duplicate FNOL from multi-source intake, reserve-must-precede-payment ordering, supervisor-authorization tiers, premature settlement, and reopen-vs-new-claim ambiguity. Use when building claim intake from caller portals, IVR, or partner systems; automating reserve-setting jobs; or integrating settlement events with finance. Trigger with "claimcenter automation", "FNOL", "claim reserve", "claim payment", "claim settlement", "claim reopen".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - claimcenter
  - fnol
  - reserves
  - payments
  - settlement
---

# Guidewire ClaimCenter Workflow

## Overview

Drive the ClaimCenter claims lifecycle through Cloud API and survive the failure modes that derail naive automation. This is the workflow used by FNOL portals, IVR claims intake, partner-of-record APIs, and reserve-setting jobs. Assumes `guidewire-install-auth` provides the bearer token and `guidewire-sdk-patterns` provides the retrying client with checksum round-trip.

Five production failures this skill prevents:

1. **Duplicate FNOL from multi-source intake** — the same loss event is reported by the caller, the claimant, and the broker; without dedup logic three claims land on the same loss with three reserves.
2. **Payment before reserve** — code creates a payment without first setting a reserve in the matching cost category; API returns `422 reserve-required`.
3. **Authorization-tier violation** — an integration with payment role `cc.payment.write` attempts a payment above its authorization limit; API returns `422 authorization-required` and the payment lands in pending-approval.
4. **Premature settlement** — claim closed before all open reserves are zeroed or all open activities resolved; reopens compound work and generate audit findings.
5. **Reopen vs. new claim confusion** — late-arriving evidence on a closed claim creates a new claim with a different number, breaking the loss-event continuity downstream finance and analytics depend on.

## Prerequisites

- A working auth + SDK layer per `guidewire-install-auth` and `guidewire-sdk-patterns`
- Cloud API roles `cc.claim.write`, `cc.reserve.write`, `cc.payment.write` assigned per least privilege; payment authorization tier matches the integration's expected payment range
- Knowledge of the carrier's loss-cause code list (`AUTO`, `PROPERTY`, `WORKERSCOMP`, etc.) and cost-category configuration (`body`, `parts`, `medical`, `legal`)
- A loss-dedup key strategy (typically: `policyNumber + lossDate + lossCause + reporterId`)

## Instructions

### 1. FNOL with deduplication

Before creating a claim, check whether one already exists for the same loss event. The dedup key combines policy, loss date, loss cause, and the reporting party.

```typescript
async function findExistingClaim(policyNumber: string, lossDate: string, lossCauseCode: string): Promise<Claim | null> {
  const url = `${BASE}/cc/rest/v1/claims?filter=policyNumber+eq+'${policyNumber}'+and+lossDate+eq+'${lossDate}'+and+lossCause.code+eq+'${lossCauseCode}'`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${await getToken()}` } });
  const body = await res.json();
  return body.data[0] ?? null;
}

const existing = await findExistingClaim(policyNumber, lossDate, lossCauseCode);
if (existing) {
  await addReporterToExistingClaim(existing.attributes.id, reporter); // additional reporter, same loss
  return { status: "deduplicated", claimNumber: existing.attributes.claimNumber };
}
const claim = await createClaim({ policyNumber, lossDate, lossCauseCode, reporter, description });
```

The dedup window is loss-cause-specific. For `AUTO`, same-day same-cause is almost certainly the same event. For `PROPERTY`, weather events can produce multiple legitimate same-cause same-day claims across distinct locations — extend the dedup key with the loss-location ZIP for that line.

### 2. Reserve setting before any payment

Reserves communicate the carrier's expected outflow per cost category. The Cloud API enforces "reserve before payment" — payments without a matching reserve return `422 reserve-required`.

```typescript
await retryable(async () => {
  const res = await fetch(`${BASE}/cc/rest/v1/claims/${claimId}/reserves`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({
      data: { attributes: {
        reserveAmount: { amount: 5000, currency: "usd" },
        costType: { code: "claimcost" },
        costCategory: { code: "body" },
        reserveLine: { exposure: { id: exposureId } },
      } },
    }),
  });
  if (!res.ok) throw await mapError(res, "POST", `/cc/rest/v1/claims/${claimId}/reserves`);
});
```

Reserve adjustments (raise/lower) use PATCH on the reserve resource; checksum round-trip applies. Lowering a reserve below cumulative payments returns `422` — fix payments first or use a reserve transfer.

### 3. Payments with authorization-tier handling

The integration's authorization tier is configured per Service Application in GCC. A payment that exceeds the tier does not error — it lands in `Status: PendingApproval` and waits for a supervisor:

```typescript
const payment = await fetch(`${BASE}/cc/rest/v1/claims/${claimId}/payments`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
  body: JSON.stringify({ data: { attributes: paymentBody } }),
}).then(r => r.json());

if (payment.data.attributes.status.code === "PendingApproval") {
  await emitPaymentEscalationEvent({ claimId, paymentId: payment.data.attributes.id, amount: paymentBody.amount });
  return { status: "pending-approval", paymentId: payment.data.attributes.id };
}
```

Do not poll the payment for completion. Subscribe to the App Event for payment-status-change and react asynchronously — this is covered in `guidewire-webhooks-integrations`.

### 4. Settlement with completeness gates

A claim should only close when every exposure has either been paid in full, denied, or has reserves zeroed; and every required activity (subro decision, salvage decision, supervisor sign-off) is completed.

```typescript
async function isReadyToSettle(claimId: string): Promise<{ ready: boolean; blockers: string[] }> {
  const claim = await getClaim(claimId, "exposures,activities,reserves");
  const blockers: string[] = [];
  for (const reserve of claim.included.reserves) {
    if (reserve.attributes.status.code === "Open" && reserve.attributes.amount.amount > 0) {
      blockers.push(`reserve ${reserve.id} is ${reserve.attributes.amount.amount} open`);
    }
  }
  for (const activity of claim.included.activities) {
    if (activity.attributes.required && activity.attributes.status.code !== "Completed") {
      blockers.push(`activity ${activity.id} (${activity.attributes.subject}) not completed`);
    }
  }
  return { ready: blockers.length === 0, blockers };
}
```

Only call the close endpoint when `isReadyToSettle` returns `ready: true`. Premature closure works but creates audit findings and forces reopens.

### 5. Reopen vs. new claim

Late-arriving evidence on a closed claim is almost always the same loss event. Reopen the existing claim rather than creating a new one — claim numbers must remain stable for the underlying loss event so finance, analytics, and regulatory reporting continue to roll up correctly.

```typescript
async function handleLateEvidence(claimNumber: string, evidence: Evidence): Promise<Result> {
  const claim = await getClaimByNumber(claimNumber);
  if (claim.attributes.status.code === "Closed") {
    await fetch(`${BASE}/cc/rest/v1/claims/${claim.attributes.id}/reopen`, {
      method: "POST",
      headers: { Authorization: `Bearer ${await getToken()}`, "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ data: { attributes: { reason: evidence.reason } } }),
    });
  }
  await attachEvidence(claim.attributes.id, evidence);
  return { status: "reopened", claimNumber };
}
```

The reopen endpoint requires a reason — log the evidence type and source so the audit trail explains why the claim was reopened.

## Output

A complete ClaimCenter workflow integration ships with all of the following:

- A FNOL function with a configurable dedup key (per loss-cause line) that returns `{ status: "created" | "deduplicated", claimNumber }`.
- Reserve-setting that runs before any payment in the same cost category, with a transfer/adjustment helper for raising or lowering reserves safely.
- Payment creation that recognizes the `PendingApproval` status and emits an escalation event rather than blocking the calling thread.
- A `isReadyToSettle()` gate that inspects reserves and required activities before allowing the close endpoint to be called.
- A reopen handler that distinguishes late evidence (reopen) from a genuinely new loss event (new claim).
- A claim-event log capturing every transition with correlation_id, idempotency_key, and reason.

## Examples

### Example 1 — FNOL with dedup

```typescript
const result = await intakeFnol({ policyNumber, lossDate, lossCauseCode, reporter, description });
if (result.status === "deduplicated") {
  return { claimNumber: result.claimNumber, message: "Loss already on file; reporter added" };
}
return { claimNumber: result.claimNumber, message: "New claim opened" };
```

### Example 2 — Reserve, payment, escalation

```typescript
await setReserve(claimId, { amount: 50000, costCategory: "medical" });
const payment = await createPayment(claimId, { amount: 35000, costCategory: "medical", payee });
if (payment.status === "pending-approval") {
  await notify("supervisor", { claimId, paymentId: payment.id, amount: 35000 });
}
```

### Example 3 — Settlement readiness check

```typescript
const { ready, blockers } = await isReadyToSettle(claimId);
if (!ready) return { status: "not-ready", blockers };
await closeClaim(claimId, { reason: "settled" });
```

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `422 reserve-required` on payment POST | no open reserve in the matching cost category | call reserve POST first, then retry the payment |
| `422 authorization-required` on payment | payment exceeds the integration's authorization tier | not an error path — the payment lands in PendingApproval; subscribe to status-change event |
| `422 reserve-below-payments` on reserve PATCH (lower) | trying to lower a reserve below the cumulative paid amount | reverse a payment first, or use a reserve transfer endpoint |
| `409 Conflict` on claim PATCH | concurrent edits | use `patchResource()` from `guidewire-sdk-patterns` |
| `422 close-blocked` on close endpoint | open reserves or incomplete required activities | run `isReadyToSettle()` before calling close |
| Two claim numbers exist for the same loss event | dedup logic is missing or the dedup key is too narrow | extend the key (add ZIP for property lines, add VIN for auto) |
| Reopen endpoint returns 422 | claim is too old (carrier-configured retention) | new claim is the only path; document the loss-event linkage in the new claim's notes |
| Late evidence created a new claim instead of reopening | code did not check existing-claim status before creating | always check `getClaimByNumber()` before `createClaim()` for late events |

For deeper coverage (subrogation tracking, salvage handling, recovery payments, multi-claimant scenarios, fraud-flagging on intake), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — bearer token and scope assignment
- `guidewire-sdk-patterns` — retrying client, checksum round-trip, idempotency
- `guidewire-core-workflow-a` — the equivalent submission→bind→issue pipeline in PolicyCenter
- `guidewire-webhooks-integrations` — App Events for payment-status-change, reserve-changed, claim-closed
- `guidewire-observability-and-incident-response` — interpreting reserve-balance and payment-pending signals in production

## Resources

- [ClaimCenter Cloud API reference](https://docs.guidewire.com/cloud/cc/202407/apiref/)
- [Cloud API claims domain guide](https://docs.guidewire.com/cloud/cc/202407/apiref/index.html#tag/Claims)
- [Guidewire ClaimCenter configuration documentation](https://docs.guidewire.com/insurancesuite/claimcenter/202407/configuration/)
