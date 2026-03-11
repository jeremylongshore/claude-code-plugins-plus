---
name: customerio-common-errors
description: |
  Diagnose and fix Customer.io common errors.
  Use when troubleshooting API errors, delivery issues,
  or integration problems with Customer.io.
  Trigger with phrases like "customer.io error", "customer.io not working",
  "debug customer.io", "customer.io issue".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Common Errors

## Overview
Diagnose and resolve common Customer.io integration errors, delivery issues, and API problems.

## Prerequisites
- Access to Customer.io dashboard
- API credentials configured
- Access to application logs

## Error Reference

| Error Code | Meaning | Action |
|------------|---------|--------|
| 400 | Bad Request | Check request format and data |
| 401 | Unauthorized | Verify API credentials |
| 403 | Forbidden | Check API key permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Rate Limited | Implement backoff |
| 500 | Server Error | Retry with backoff |

## Instructions

### Step 1: Identify the Error Category
Check error response code and message. Authentication errors (401/403) need credential review. Request errors (400) need payload fixes. Rate limits (429) need backoff logic.

### Step 2: Fix Authentication Issues
Verify correct API key type (Track vs App). Check environment variables are loaded. Ensure credentials match the workspace.

### Step 3: Fix Request Errors
Check for empty user IDs, millisecond timestamps (use Unix seconds), and malformed email addresses. Validate payloads before sending.

### Step 4: Handle Rate Limiting
Implement exponential backoff with jitter. Start at 1s delay and double on each retry. Skip retries on 4xx errors (except 429).

### Step 5: Debug Delivery Issues
Check user activity in dashboard, verify campaign is active and user matches segment, review suppression list, and check message preview.

### Step 6: Fix SDK-Specific Errors
For Node.js, check env vars exist before creating client. For Python, catch both `CustomerIOError` and `ConnectionError`.

For detailed code examples and diagnostic commands, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Diagnostic Commands
```bash
# Check API connectivity
curl -X POST "https://track.customer.io/api/v1/customers/test-user" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  -w "\nHTTP Status: %{http_code}\n"
```

## Error Handling
| Issue | Solution |
|-------|----------|
| Events not triggering campaigns | Check exact event name (case-sensitive) |
| User not in segment | Verify required attributes and types |
| SDK initialization error | Check env vars exist before creating client |

## Resources
- [API Error Reference](https://customer.io/docs/api/track/#section/Errors)
- [Troubleshooting Guide](https://customer.io/docs/troubleshooting/)
- [Status Page](https://status.customer.io/)

## Next Steps
After resolving errors, proceed to `customerio-debug-bundle` for comprehensive debug reports.
