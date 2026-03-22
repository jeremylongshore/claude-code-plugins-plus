---
name: finta-common-errors
description: |
  Diagnose and fix Finta common errors and exceptions.
  Use when encountering Finta errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "finta error", "fix finta",
  "finta not working", "debug finta".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, finta]
---

# Finta Common Errors

## Overview

Quick reference for the top 10 most common Finta errors and their solutions.


## Prerequisites
- Finta SDK installed
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

### Transaction Declined
**Error Message:**
```
402 Payment Required: Transaction declined — insufficient_funds
```

**Cause:** Account balance or card limit insufficient for the transaction amount.

**Solution:**
```bash
# Check available balance before initiating
const balance = await client.accounts.balance();
# Set up auto-reload thresholds
# For card transactions — check card limit, not just account balance

```

---

### Idempotency Conflict
**Error Message:**
```
409 Conflict: Idempotency key already used with different parameters
```

**Cause:** Same idempotency key sent with different request body (retry with changed params).

**Solution:**
# Generate unique idempotency key per transaction attempt
const idempotencyKey = `txn-${orderId}-${Date.now()}`;
# For retries, use the SAME key with the SAME parameters
# Different amounts/recipients need different keys


---

### Webhook Signature Invalid
**Error Message:**
```
401 Unauthorized: Webhook signature verification failed
```

**Cause:** HMAC signature doesn't match — wrong webhook secret or tampered payload.

**Solution:**
```typescript
# Verify you're using the webhook signing secret (not API key)
const isValid = crypto.timingSafeEqual(
  Buffer.from(computedSignature),
  Buffer.from(headerSignature)
);
# Use raw request body for signature verification (not parsed JSON)

```



## Examples

### Quick Diagnostic Commands
```bash
# Check Finta status
curl -s https://status.finta.com

# Verify API connectivity
curl -I https://api.finta.com

# Check local configuration
env | grep FINTA
```

### Escalation Path
1. Collect evidence with `finta-debug-bundle`
2. Check Finta status page
3. Contact support with request ID

## Resources
- [Finta Status Page](https://status.finta.com)
- [Finta Support](https://docs.finta.com/support)
- [Finta Error Codes](https://docs.finta.com/errors)

## Next Steps
For comprehensive debugging, see `finta-debug-bundle`.