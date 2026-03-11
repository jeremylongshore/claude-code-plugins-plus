---
name: guidewire-core-workflow-a
description: |
  Execute Guidewire primary workflow: Policy lifecycle management in PolicyCenter.
  Use when implementing quoting, binding, issuing, endorsing, or renewing policies.
  Trigger with phrases like "policycenter workflow", "create policy",
  "bind submission", "issue policy", "policy endorsement", "quote insurance".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Core Workflow A: Policy Lifecycle

## Overview

Master the complete policy lifecycle in PolicyCenter: submission creation, quoting, binding, issuance, endorsements, and renewals.

## Prerequisites

- Completed `guidewire-install-auth` and `guidewire-sdk-patterns`
- Understanding of P&C insurance concepts
- Valid API credentials with policy admin permissions

## Policy Lifecycle States

```
Submission -> Quote -> Bind -> Issue -> In-Force -> Endorsement/Renewal/Cancellation
  [Draft]   [Quoted]  [Bound] [Issued]  [Active Policy]
```

## Instructions

### Step 1: Create Account

POST to `/account/v1/accounts` with account holder contact details (name, DOB, address) and producer code assignment.

### Step 2: Create Submission

POST to `/job/v1/submissions` with account ID, base state, effective date, product code (e.g., `PersonalAuto`), and producer code.

### Step 3: Add Vehicles and Coverages

POST vehicles to the submission's policy period, then add coverages per vehicle: liability, collision, comprehensive, and medical payments.

### Step 4: Add Drivers

POST driver details (name, DOB, license) to the policy period.

### Step 5: Quote the Submission

POST to `/job/v1/submissions/{id}/quote` to trigger rating. Retrieve premium breakdown from the policy period.

### Step 6: Bind the Policy

POST to `/job/v1/submissions/{id}/bind`. Verify status is `Bound` and capture the policy number.

### Step 7: Issue the Policy

POST to `/job/v1/submissions/{id}/issue`. The policy is now in-force.

For complete TypeScript API calls and Gosu server-side implementations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Created account with account holder details
- Submission with unique job number
- Quote with premium breakdown
- Bound and issued policy with policy number

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Validation failed` | Missing required data | Check all required fields |
| `Cannot quote` | Invalid policy configuration | Review coverages and limits |
| `Cannot bind` | Outstanding issues | Resolve all validation errors |
| `UW hold` | Requires underwriting approval | Process UW referrals |
| `Rating error` | Rating engine failure | Check rate tables and factors |

## Resources

- [PolicyCenter Cloud API](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Submission Workflow Guide](https://docs.guidewire.com/cloud/pc/202503/cloudapica/)
- [Policy Lifecycle Documentation](https://docs.guidewire.com/education/)

## Next Steps

For claims processing workflow, see `guidewire-core-workflow-b`.

## Examples

**Basic usage**: Apply guidewire core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire core workflow a for production environments with multiple constraints and team-specific requirements.