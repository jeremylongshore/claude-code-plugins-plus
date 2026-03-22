---
name: flexport-common-errors
description: |
  Diagnose and fix Flexport common errors and exceptions.
  Use when encountering Flexport errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "flexport error", "fix flexport",
  "flexport not working", "debug flexport".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flexport]
---

# Flexport Common Errors

## Overview

Quick reference for the top 10 most common Flexport errors and their solutions.


## Prerequisites
- Flexport SDK installed
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

### Insufficient Permissions
**Error Message:**
```
403 Forbidden: API key lacks 'entities.write' scope
```

**Cause:** API token doesn't have the required OAuth scope or RBAC role.

**Solution:**
```bash
# Check required scopes in API docs
# Re-create token with correct scopes
# Enterprise platforms often require admin to approve API access
# Some operations need org-level admin, not just workspace-level

```

---

### Entity Validation Failed
**Error Message:**
```
422 Unprocessable Entity: Field 'industry_code' must match pattern ^[A-Z]{2}\d{4}$
```

**Cause:** Domain-specific validation rules on entity fields (industry codes, formats, ranges).

**Solution:**
# Fetch field validation rules: client.schema.get('entity_type')
# Enterprise platforms have strict domain-specific validations
# Pre-validate data against schema before API submission


---

### Concurrent Modification
**Error Message:**
```
409 Conflict: Entity was modified by another process (version mismatch)
```

**Cause:** Optimistic locking — another user or integration updated the entity since you read it.

**Solution:**
```typescript
# Read latest version before update (optimistic concurrency)
const latest = await client.entities.get(id);
await client.entities.update(id, { ...changes, version: latest.version });
# Implement retry with re-read on 409

```



## Examples

### Quick Diagnostic Commands
```bash
# Check Flexport status
curl -s https://status.flexport.com

# Verify API connectivity
curl -I https://api.flexport.com

# Check local configuration
env | grep FLEXPORT
```

### Escalation Path
1. Collect evidence with `flexport-debug-bundle`
2. Check Flexport status page
3. Contact support with request ID

## Resources
- [Flexport Status Page](https://status.flexport.com)
- [Flexport Support](https://docs.flexport.com/support)
- [Flexport Error Codes](https://docs.flexport.com/errors)

## Next Steps
For comprehensive debugging, see `flexport-debug-bundle`.