---
name: guidewire-core-workflow-a
description: |
  Execute Guidewire primary workflow: Policy lifecycle in PolicyCenter.
  Use when implementing quoting, binding, issuing, endorsing, or renewing policies.
  Trigger: "policycenter workflow", "create policy", "bind submission", "issue policy".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Core Workflow A: Policy Lifecycle

## Overview

The complete policy lifecycle in PolicyCenter: account creation, submission, quoting, binding, issuance, endorsements, and renewals via Cloud API.

## Policy Lifecycle States

```
Account -> Submission -> Quote -> Bind -> Issue -> In-Force
                                                    |
                                          Endorse / Renew / Cancel
```

## Instructions

### Step 1: Create Account

```typescript
const account = await fetch(`${GW_PC}/account/v1/accounts`, {
  method: 'POST', headers,
  body: JSON.stringify({
    data: { attributes: {
      accountHolderContact: {
        firstName: 'John', lastName: 'Smith',
        primaryAddress: { addressLine1: '123 Main St', city: 'Atlanta', state: 'GA', postalCode: '30301' },
        dateOfBirth: '1985-03-15',
      },
      producerCodes: [{ id: 'pc:100' }],
    }}
  }),
}).then(r => r.json());
console.log(`Account: ${account.data.attributes.accountNumber}`);
```

### Step 2: Create Submission

```typescript
const submission = await fetch(`${GW_PC}/job/v1/submissions`, {
  method: 'POST', headers,
  body: JSON.stringify({
    data: { attributes: {
      account: { id: account.data.id },
      baseState: 'GA', effectiveDate: '2025-04-01',
      product: { code: 'PersonalAuto' },
      producerCode: { id: 'pc:100' },
    }}
  }),
}).then(r => r.json());
```

### Step 3: Quote -> Bind -> Issue

```typescript
// Quote the submission
await fetch(`${GW_PC}/job/v1/submissions/${submission.data.id}/quote`, { method: 'POST', headers });

// Bind
await fetch(`${GW_PC}/job/v1/submissions/${submission.data.id}/bind`, { method: 'POST', headers });

// Issue
await fetch(`${GW_PC}/job/v1/submissions/${submission.data.id}/issue`, { method: 'POST', headers });
console.log('Policy issued successfully');
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot quote` | Missing coverages/vehicles | Add required data before quoting |
| `UW hold` | Underwriting referral | Process UW approval in PolicyCenter |
| `Rating error` | Rate table issue | Check product configuration |

For detailed Gosu and API examples, see: [implementation guide](references/implementation-guide.md)

## Resources

- [PolicyCenter Cloud API](https://docs.guidewire.com/cloud/pc/202503/apiref/)

## Next Steps

For claims processing, see `guidewire-core-workflow-b`.
