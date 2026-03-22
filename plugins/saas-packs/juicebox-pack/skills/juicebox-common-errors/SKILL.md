---
name: juicebox-common-errors
description: |
  Diagnose and fix Juicebox common errors and exceptions.
  Use when encountering Juicebox errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "juicebox error", "fix juicebox",
  "juicebox not working", "debug juicebox".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Common Errors

## Overview

Quick reference for the most common Juicebox errors: duplicate records, rate limits, validation failures, and sync conflicts.


## Prerequisites
- Juicebox SDK installed
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
# Check Juicebox status
curl -s https://status.juicebox.com

# Verify API connectivity
curl -I https://api.juicebox.com

# Check local configuration
env | grep JUICEBOX
```

### Escalation Path
1. Collect evidence with `juicebox-debug-bundle`
2. Check Juicebox status page
3. Contact support with request ID

## Resources
- [Juicebox Status Page](https://status.juicebox.com)
- [Juicebox Support](https://docs.juicebox.com/support)
- [Juicebox Error Codes](https://docs.juicebox.com/errors)

## Next Steps
For comprehensive debugging, see `juicebox-debug-bundle`.