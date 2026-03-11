---
name: customerio-primary-workflow
description: |
  Execute Customer.io primary messaging workflow.
  Use when setting up email campaigns, push notifications,
  SMS messaging, or in-app message workflows.
  Trigger with phrases like "customer.io campaign", "customer.io workflow",
  "customer.io email automation", "customer.io messaging".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Primary Workflow

## Overview
Implement Customer.io's primary messaging workflow: identify users, track events, and trigger automated campaigns.

## Prerequisites
- Customer.io SDK configured
- Campaign/workflow created in Customer.io dashboard
- Understanding of your user lifecycle events

## Instructions

### Step 1: Define User Lifecycle Events
### Step 2: Implement Event Tracking Service
### Step 3: Integrate with Application
### Step 4: Create Dashboard Campaign

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`
In Customer.io Dashboard:
1. Go to Campaigns > Create Campaign
2. Select trigger: Event "signed_up"
3. Add workflow steps:
   - Wait 1 day
   - Send welcome email
   - Wait 3 days
   - Branch: if email_verified = false, send reminder
   - Continue nurture sequence

## Output
- User lifecycle event definitions
- Customer.io service integration
- Application route integration
- Campaign workflow triggering

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Event not triggering | Wrong event name | Match exact event name in dashboard |
| User not receiving | Missing email attribute | Ensure email is set on identify |
| Duplicate sends | Multiple event fires | Deduplicate or use idempotency |

## Resources
- [Customer.io Campaigns](https://customer.io/docs/campaigns/)
- [Trigger Events](https://customer.io/docs/events/)

## Next Steps
After implementing primary workflow, proceed to `customerio-core-feature` for advanced features.
