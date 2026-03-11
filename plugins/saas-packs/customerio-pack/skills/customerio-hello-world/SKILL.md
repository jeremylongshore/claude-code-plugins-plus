---
name: customerio-hello-world
description: |
  Create a minimal working Customer.io example.
  Use when learning Customer.io basics, testing SDK setup,
  or creating your first messaging integration.
  Trigger with phrases like "customer.io hello world", "first customer.io message",
  "test customer.io", "customer.io example".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Hello World

## Overview
Create a minimal working Customer.io example that identifies a user and triggers an event.

## Prerequisites
- Completed `customerio-install-auth` skill
- Customer.io SDK installed
- Valid Site ID and API Key configured

## Instructions

### Step 1: Create Basic Integration
### Step 2: Run the Example
### Step 3: Verify in Dashboard

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`
1. Go to Customer.io dashboard
2. Navigate to People section
3. Search for "user-123" or "hello@example.com"
4. Verify user profile shows attributes
5. Check Activity tab for "hello_world" event

## Output
- User created/updated in Customer.io
- Event recorded in user's activity log
- Console output confirming success

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid credentials | Verify Site ID and API Key |
| 400 Bad Request | Invalid data format | Check attribute names and types |
| User not found | Identify not called | Always identify before tracking events |
| Event not showing | Dashboard delay | Wait 1-2 minutes and refresh |

## Examples

### Python Hello World
### With Anonymous User
## Resources
- [Identify API](https://customer.io/docs/api/track/#operation/identify)
- [Track API](https://customer.io/docs/api/track/#operation/track)

## Next Steps
After verifying hello world works, proceed to `customerio-local-dev-loop` to set up your development workflow.