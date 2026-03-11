---
name: customerio-local-dev-loop
description: |
  Configure Customer.io local development workflow.
  Use when setting up local testing, development environment,
  or offline development for Customer.io integrations.
  Trigger with phrases like "customer.io local dev", "test customer.io locally",
  "customer.io development environment", "customer.io sandbox".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Local Dev Loop

## Overview
Set up an efficient local development workflow for Customer.io integrations with proper testing and isolation.

## Prerequisites
- Customer.io SDK installed
- Separate development workspace in Customer.io (recommended)
- Environment variable management tool (dotenv)

## Instructions

### Step 1: Create Environment Configuration
### Step 2: Create Dev Client Wrapper
### Step 3: Set Up Test Helpers
### Step 4: Create Dev Scripts

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Environment-aware Customer.io client
- Dry-run mode for safe testing
- Test mocks for unit testing
- Prefixed events for development isolation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Env vars not loaded | Use dotenv or env-specific files |
| Dev events in prod | Environment check failed | Verify NODE_ENV is set correctly |
| Mock not working | Import order issue | Mock before importing client |

## Resources
- [Customer.io Workspaces](https://customer.io/docs/workspaces/)
- [Test Mode Best Practices](https://customer.io/docs/test-mode/)

## Next Steps
After setting up local dev, proceed to `customerio-sdk-patterns` for production-ready patterns.
