---
name: instantly-common-errors
description: |
  Diagnose and fix Instantly common errors and exceptions.
  Use when encountering Instantly errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "instantly error", "fix instantly",
  "instantly not working", "debug instantly".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, instantly]
---

# Instantly Common Errors

## Overview

Quick reference for the most common Instantly errors: duplicate records, rate limits, validation failures, and sync conflicts.


## Prerequisites
- Instantly SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

### Duplicate Record
**Error Message:**
```
409 Conflict: A contact with email user@example.com already exists
```

**Cause:** Attempting to create a record that matches an existing unique field (email, phone).

**Solution:**
```bash
# Use upsert endpoint instead of create
await client.contacts.upsert({ email: 'user@example.com', ...data });
# Or search first: client.contacts.search({ email: 'user@example.com' })

```

---

### API Rate Limit (Burst)
**Error Message:**
```
429 Too Many Requests: Retry after 10 seconds
```

**Cause:** Exceeded per-second or per-minute API rate limit. CRM APIs have tight burst limits.

**Solution:**
# Use batch endpoints for bulk operations (100 records per call)
# Implement retry with Retry-After header value
# Space requests: max 10 req/s for most CRM APIs


---

### Required Field Missing
**Error Message:**
```
422 Unprocessable Entity: 'email' is required for contact creation
```

**Cause:** Missing a mandatory field defined in CRM configuration.

**Solution:**
```typescript
# Check required fields: client.schema.get('contact')
# Required fields vary by CRM configuration — check admin settings
# Map incoming data to all required fields before batch import

```


---

### Duplicate Record on Import
**Error Message:**
```
409 Conflict: Contact with email user@example.com already exists (id: abc-123)
```

**Cause:** Attempting to create a record with an email/phone that matches an existing contact.

**Solution:**
Use the upsert endpoint instead of create: `client.contacts.upsert({ email, ...data })`. Or search first and merge if found.


## Examples

### Quick Diagnostic Commands
```bash
# Check Instantly status
curl -s https://status.instantly.com

# Verify API connectivity
curl -I https://api.instantly.com

# Check local configuration
env | grep INSTANTLY
```

### Escalation Path
1. Collect evidence with `instantly-debug-bundle`
2. Check Instantly status page
3. Contact support with request ID

## Resources
- [Instantly Status Page](https://status.instantly.com)
- [Instantly Support](https://docs.instantly.com/support)
- [Instantly Error Codes](https://docs.instantly.com/errors)

## Next Steps
For comprehensive debugging, see `instantly-debug-bundle`.