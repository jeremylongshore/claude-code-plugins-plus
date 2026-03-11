---
name: guidewire-core-workflow-b
description: |
  Execute Guidewire secondary workflow: Claims processing in ClaimCenter.
  Use when implementing FNOL, claim investigation, reserves, payments, and settlement.
  Trigger with phrases like "claimcenter workflow", "create claim", "file fnol",
  "process claim", "claim settlement", "claim payment".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Core Workflow B: Claims Processing

## Overview

Master the complete claims lifecycle in ClaimCenter: First Notice of Loss (FNOL), claim investigation, reserve setting, payments, and settlement.

## Prerequisites

- Completed `guidewire-install-auth` and `guidewire-core-workflow-a`
- Understanding of claims handling processes
- Valid API credentials with claims admin permissions

## Claims Lifecycle States

```
FNOL -> Open -> Investigation -> Evaluation -> Negotiation -> Settlement -> Closed
[Draft] [Open]   [Reserve]      [Exposure]    [Payment]     [Settle]    [Closed]
```

## Instructions

### Step 1: Create FNOL

POST to `/fnol/v1/fnol` with loss date, loss type/cause, description, policy number, loss location, and reporter details.

### Step 2: Add Exposures

POST exposures to `/claim/v1/claims/{id}/exposures` specifying exposure type (`VehicleDamage`, `BodilyInjury`), loss party (`insured`, `claimant`), and primary coverage.

### Step 3: Add Incidents

POST vehicle incidents with severity, damage description, vehicle details, and operability status.

### Step 4: Set Reserves

POST reserves to each exposure specifying reserve line (`indemnity`, `expenses`), cost type, category, and amount.

### Step 5: Create Payments

POST payments with payment type (`partial`, `final`), exposure reference, payee, reserve line, amount, and payment method (`check`).

### Step 6: Close Exposures

POST to each exposure's `/close` endpoint with the closed outcome (`completed`, `denied`, `duplicate`).

### Step 7: Close Claim

POST to `/claim/v1/claims/{id}/close` with outcome. All exposures must be closed first.

For complete TypeScript API calls and Gosu server-side implementations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- FNOL claim with claim number
- Exposures linked to coverages
- Reserves set on exposures
- Payments processed
- Claim closed with outcome

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Policy not found` | Invalid policy number | Verify policy number and status |
| `Coverage not applicable` | Wrong coverage type | Check policy coverages |
| `Reserve exceeds limit` | Over policy limit | Adjust to policy limits |
| `Payment validation` | Missing required fields | Check payee and amount |
| `Cannot close` | Open activities/exposures | Complete pending items |

## Resources

- [ClaimCenter Cloud API](https://docs.guidewire.com/cloud/cc/202503/apiref/)
- [Claims Workflow Guide](https://docs.guidewire.com/cloud/cc/202503/cloudapica/)
- [Exposure Types Reference](https://docs.guidewire.com/education/)

## Next Steps

For error handling patterns, see `guidewire-common-errors`.

## Examples

**Basic usage**: Apply guidewire core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire core workflow b for production environments with multiple constraints and team-specific requirements.