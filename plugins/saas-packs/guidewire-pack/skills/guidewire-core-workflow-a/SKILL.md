---
name: guidewire-core-workflow-a
description: Automate the PolicyCenter account→submission→quote→bind→issue→endorse→renew pipeline including the failure paths — underwriting issues blocking bind, quotes expiring before bind, referrals stuck pending approval, and mid-term endorsements that trigger unexpected premium audit recalculation. Use when building outbound integrations against PolicyCenter Cloud API (CRM-driven submission, broker-portal binding, automated renewal jobs). Trigger with "policycenter automation", "submission to bind", "policy renewal", "policy endorsement", "underwriting issue".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - policycenter
  - underwriting
  - submission
  - renewal
  - endorsement
---

# Guidewire PolicyCenter Workflow

## Overview

Drive the PolicyCenter policy lifecycle through Cloud API and survive the state-transition failures that derail naive automation. This is the workflow used by broker portals to quote-and-bind, by CRMs to push submissions, and by renewal jobs to issue out-of-cycle. Assumes `guidewire-install-auth` provides the bearer token and `guidewire-sdk-patterns` provides the retrying client with checksum round-trip.

Five production failures this skill prevents:

1. **Bind on a quote with open UW issues** — quote API returns `200`, the `underwritingIssues[]` array is non-empty, the client ignores it, bind returns `422 rule-violation`.
2. **Bind on a stale quote** — quotes expire (default 30 days). A submission left open over a holiday returns `422 quote-expired` on bind.
3. **Orphaned submissions on partial failure** — submission → quote succeeds, bind fails, no rollback; the submission sits in `Quoted` status forever, blocking the next attempt.
4. **Renewal outside the renewal window** — calling renewal before the window opens (typically 60–90 days before expiration) returns `422 renewal-window-closed`.
5. **Endorsement premium drift** — mid-term endorsement recalculates premium against current rate plans, which may differ from the rate plan in force at policy inception. The numeric difference surprises downstream finance integrations.

## Prerequisites

- A working auth + SDK layer per `guidewire-install-auth` and `guidewire-sdk-patterns` (`getToken()`, `patchResource()`, `paginate()`, `mapError()`)
- Cloud API roles `pc.account.write`, `pc.submission.write`, `pc.policy.write` assigned to the integration's Service Application
- Knowledge of which **product code** drives the workflow (e.g., `PersonalAuto`, `BOPLine`) — submission shape is product-specific
- For renewal jobs: read access to the renewal-window configuration on the relevant product

## Instructions

Build the workflow as discrete state-transition functions, each fully responsible for surfacing the failure modes of its transition. Compose them with explicit checkpoints — never collapse the pipeline into a single fire-and-forget call.

### 1. Create the account

```typescript
const idempotencyKey = crypto.randomUUID();
const account = await retryable(async () => {
  const res = await fetch(`${BASE}/pc/rest/v1/accounts`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ data: { attributes: { accountHolderContact: contact, primaryLocation: address } } }),
  });
  if (!res.ok) throw await mapError(res, "POST", "/pc/rest/v1/accounts");
  return (await res.json()).data;
});
```

The Idempotency-Key prevents duplicate accounts on retry. Persist `account.attributes.accountNumber` and the resource id immediately — both are needed downstream and the resource id is not derivable from the number.

### 2. Create the submission against the account

Submission is product-specific; its `attributes` shape varies. Read the product's submission schema from the API reference rather than hardcoding fields. The submission moves to `Draft` on creation.

```typescript
const submission = await createSubmission(account.attributes.id, {
  productCode: "PersonalAuto",
  effectiveDate: "2026-06-01",
});
```

### 3. Quote the submission and inspect underwriting issues

The most-skipped step in naive automation. The quote response embeds `underwritingIssues[]`; non-empty with `blocksBind: true` means bind will fail.

```typescript
const quoted = await fetch(`${BASE}/pc/rest/v1/jobs/${submission.attributes.id}/quote`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}`, "Idempotency-Key": idempotencyKey },
});
const body = (await quoted.json()).data;
const blockingIssues = body.attributes.underwritingIssues?.filter((u: any) => u.blocksBind) ?? [];
if (blockingIssues.length) {
  await routeToReferralQueue(submission, blockingIssues);
  return { status: "referred", issues: blockingIssues };
}
```

Some UW issues are informational and bind succeeds anyway; check the boolean per issue, not the array length. Surface blocking issues to the manual review queue with the originating actor's identity so the underwriter has context.

### 4. Bind within the quote validity window

Quotes carry `attributes.quoteExpirationDate`. Past it, bind returns `422 quote-expired`. Re-quote rather than retry.

```typescript
if (new Date(body.attributes.quoteExpirationDate) < new Date()) {
  return retryQuoteAndBind(submission.attributes.id);
}
const bound = await bindSubmission(submission.attributes.id);
```

After bind, the submission status moves to `Bound` and a Policy resource is created. `bound.attributes.policy.id` is the canonical policy reference for issuance, endorsement, and renewal.

### 5. Issue (commit the bound policy to in-force)

Bind alone does not put the policy in force; issuance is a separate transition. A bound-but-not-issued policy is invisible to billing; downstream invoices will not generate.

```typescript
const issued = await fetch(`${BASE}/pc/rest/v1/policies/${bound.attributes.policy.id}/issue`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}`, "Idempotency-Key": idempotencyKey },
});
```

### 6. Endorsement with premium-drift detection

```typescript
const endorsement = await openEndorsement(policyId, effectiveDate);
const requoted = await quoteEndorsement(endorsement.attributes.id);
const oldPremium = currentPolicy.attributes.totalPremium;
const newPremium = requoted.attributes.totalPremium;
if (Math.abs(newPremium - oldPremium) > MATERIAL_DRIFT_THRESHOLD) {
  await emitPremiumDriftEvent({ policyId, oldPremium, newPremium, delta: newPremium - oldPremium });
}
const boundEndorsement = await bindEndorsement(endorsement.attributes.id);
```

Threshold is policy-dependent; finance teams typically want any drift over a few hundred dollars surfaced before bind. Do not silently bind material drifts — they show up as billing surprises.

### 7. Renewal within the renewal window

The renewal window is configured per product line. Hardcoding 60 days is wrong for any product with non-default settings; read the configuration or accept rejection from the API and respond to the `renewal-window-closed` error type.

```typescript
const policy = await fetch(`${BASE}/pc/rest/v1/policies/${policyId}`).then(r => r.json());
const expirationDate = new Date(policy.data.attributes.expirationDate);
const renewalWindowOpens = subDays(expirationDate, 60);
if (new Date() < renewalWindowOpens) throw new Error("renewal-window-not-yet-open");
const renewalJob = await fetch(`${BASE}/pc/rest/v1/policies/${policyId}/renew`, { method: "POST" });
```

## Output

A complete PolicyCenter workflow integration ships with all of the following:

- Discrete state-transition functions: `createAccount`, `createSubmission`, `quoteSubmission`, `bindSubmission`, `issuePolicy`, `openEndorsement`, `bindEndorsement`, `renewPolicy` — each handling its own failures.
- A blocking-UW-issue check before every bind attempt that routes referrals to a manual-review queue rather than retrying.
- Quote-expiry detection that re-quotes rather than retrying a stale quote.
- Premium-drift detection on endorsement with a configurable threshold and a finance-integration event emission.
- Idempotency-Keys generated once per logical operation (one per submission, one per endorsement, one per renewal cycle), reused across retries.
- A submission/policy state-transition log that captures every API response — debugging "why is this stuck" requires the full transition history.

## Examples

### Example 1 — End-to-end happy path

```typescript
const account = await createAccount(contact, address);
const submission = await createSubmission(account.attributes.id, { productCode: "PersonalAuto", effectiveDate });
const quoted = await quoteSubmission(submission.attributes.id);
if (quoted.blockingIssues.length) return { status: "referred", issues: quoted.blockingIssues };
const bound = await bindSubmission(submission.attributes.id);
const issued = await issuePolicy(bound.attributes.policy.id);
return { status: "issued", policyNumber: issued.attributes.policyNumber };
```

### Example 2 — Referred submission resumption

```typescript
// Resume after underwriter approves the referral asynchronously
const submission = await getSubmission(submissionId);
if (submission.attributes.underwritingIssues.every(u => u.status === "Approved")) {
  const requoted = await quoteSubmission(submissionId); // re-quote required after referral resolution
  return await bindAndIssue(requoted);
}
```

### Example 3 — Renewal with window check

```typescript
const policy = await getPolicy(policyId);
const window = await getRenewalWindow(policy.attributes.productCode);
if (!isWithinWindow(policy.attributes.expirationDate, window)) {
  return { status: "deferred", reason: "renewal-window-not-yet-open", retryAfter: window.opensOn };
}
const renewal = await renewPolicy(policyId);
return { status: "renewed", newPolicyId: renewal.attributes.id };
```

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `422` with `errors[].type === "rule-violation"` on bind | unaddressed blocking UW issue | inspect `quoted.attributes.underwritingIssues`; never retry; route to manual review |
| `422 quote-expired` on bind | quote past `quoteExpirationDate` | re-quote the submission; do not retry the bind directly |
| `422 renewal-window-closed` | renewal initiated outside the configured window | back off until the window opens; surface `retryAfter` to the caller |
| `422 submission-state-invalid` | trying to bind a submission still in `Draft` | call quote first; the state machine is enforced server-side |
| `409 Conflict` on PATCH of submission | another job edited the submission concurrently | use `patchResource()` from `guidewire-sdk-patterns` to handle checksum round-trip |
| Bound policy never reaches In Force | bind was called but issue was not | issue is a separate API call after bind — both are required |
| Endorsement premium differs materially from expected | rate plan changed between policy inception and endorsement effective date | surface the drift to finance before binding; do not silently absorb the delta |
| Submission stuck in Quoted after a failed bind | partial-failure orphan | resume by checking `underwritingIssues` and re-attempting bind, or withdraw via the `withdraw` endpoint |

For deeper coverage (custom product schemas, line-of-business-specific submission shapes, multi-policy bind, broker hierarchy authorization), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-install-auth` — bearer token and scope assignment for the workflow
- `guidewire-sdk-patterns` — retrying client, checksum round-trip, idempotency, error mapping
- `guidewire-core-workflow-b` — the equivalent FNOL→reserve→settle pipeline in ClaimCenter
- `guidewire-webhooks-integrations` — listening to App Events that fire on bind, issue, and renewal transitions
- `guidewire-observability-and-incident-response` — interpreting referral-queue depth and bind-failure signals in production

## Resources

- [PolicyCenter Cloud API reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Cloud API jobs API](https://docs.guidewire.com/cloud/pc/202503/apiref/index.html#tag/Jobs)
- [Guidewire product-model documentation](https://docs.guidewire.com/insurancesuite/policycenter/202503/configuration/product/)
