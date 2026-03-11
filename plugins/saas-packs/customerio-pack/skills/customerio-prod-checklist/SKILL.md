---
name: customerio-prod-checklist
description: |
  Execute Customer.io production deployment checklist.
  Use when preparing for production launch, reviewing
  integration quality, or performing pre-launch audits.
  Trigger with phrases like "customer.io production", "customer.io checklist",
  "deploy customer.io", "customer.io go-live".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Production Checklist

## Overview
Comprehensive checklist for deploying Customer.io integrations to production covering credentials, integration quality, campaigns, deliverability, monitoring, and rollback.

## Prerequisites
- Customer.io integration complete
- Access to production credentials
- Testing completed in staging environment

## Production Checklist Summary

| Category | Key Items |
|----------|-----------|
| Credentials | Prod keys in secrets manager, correct region |
| Integration | Email attribute set, snake_case events, Unix timestamps |
| Campaigns | Sender verified, SPF/DKIM/DMARC, unsubscribe links |
| Deliverability | Domain authenticated, bounce/complaint handling |
| Monitoring | Error rate alerts, delivery metrics dashboard |
| Testing | End-to-end, smoke tests, load tests |
| Documentation | Runbooks, event catalog, escalation path |
| Rollback | Feature flags, backup messaging, notification plan |

## Go-Live Procedure

1. **T-24h**: Final staging validation
2. **T-12h**: Production smoke tests
3. **T-1h**: Enable integration with feature flag
4. **T-0**: Go live with 10% traffic
5. **T+1h**: Verify metrics, increase to 50%
6. **T+2h**: Full traffic if healthy
7. **T+24h**: Post-launch review

## Instructions

### Step 1: Verify Credentials
Confirm production Site ID and API Key are configured, stored in secrets manager, and different from dev/staging.

### Step 2: Audit Integration Quality
Run integration audit script checking email attributes, event naming, timestamps, PII handling, and error handling.

### Step 3: Review Campaign Configuration
Verify sender email, SPF/DKIM/DMARC, unsubscribe links, CAN-SPAM compliance, and test sends.

### Step 4: Set Up Monitoring and Alerts
Configure alerts for API error rate (>1%), bounce rate (>5%), complaint rate (>0.1%), and p99 latency (>5s).

### Step 5: Run Smoke Tests
Execute production smoke tests verifying API connectivity and event tracking.

### Step 6: Prepare Rollback Plan
Document rollback triggers, steps, and contacts. Set up feature flags for quick disable.

For detailed audit scripts, smoke test commands, and monitoring configuration, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Solution |
|-------|----------|
| Smoke test fails | Check credentials and network |
| High error rate post-launch | Trigger rollback procedure |
| Deliverability issues | Review sender reputation |

## Resources
- [Customer.io Launch Checklist](https://customer.io/docs/launch-checklist/)
- [Email Deliverability Guide](https://customer.io/docs/deliverability/)

## Next Steps
After production launch, proceed to `customerio-upgrade-migration` for SDK maintenance.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [deployment implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply customerio prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio prod checklist for production environments with multiple constraints and team-specific requirements.