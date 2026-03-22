---
name: wispr-common-errors
description: |
  Diagnose and fix Wispr common errors and exceptions.
  Use when encountering Wispr errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "wispr error", "fix wispr",
  "wispr not working", "debug wispr".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr Common Errors

## Overview

Quick reference for the most common Wispr API errors: authentication failures, rate limits, context length issues, and model availability.


## Prerequisites
- Wispr SDK installed
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

### Rate Limit / Token Quota Exceeded
**Error Message:**
```
429 Too Many Requests: rate_limit_exceeded
```

**Cause:** Exceeded requests-per-minute or tokens-per-minute quota for your plan.

**Solution:**
```bash
# Check current usage
curl -H "Authorization: Bearer $API_KEY" https://api.vendor.com/usage
# Implement exponential backoff with jitter
# Upgrade plan if consistently hitting limits

```

---

### Context Length Exceeded
**Error Message:**
```
400 Bad Request: This model's maximum context length is 128000 tokens. You requested 135421 tokens.
```

**Cause:** Combined prompt + max_tokens exceeds the model's context window.

**Solution:**
# Count tokens before sending
const tokenCount = encode(prompt).length;
if (tokenCount > MODEL_CONTEXT - MAX_RESPONSE) {
  prompt = truncateToFit(prompt, MODEL_CONTEXT - MAX_RESPONSE);
}


---

### Invalid API Key
**Error Message:**
```
401 Unauthorized: Invalid API key provided
```

**Cause:** API key is missing, expired, revoked, or copied with extra whitespace.

**Solution:**
```typescript
# Verify key format (should start with sk- or similar prefix)
echo $API_KEY | head -c 8
# Regenerate from dashboard if expired
# Check for trailing newlines: echo -n "$API_KEY" | wc -c

```


---

### Content Moderation / Safety Filter
**Error Message:**
```
400 Bad Request: Content policy violation — output blocked by safety filter
```

**Cause:** Model output triggered content policy filters or input contained restricted content.

**Solution:**
Review your system prompt for policy-compliant framing. Use moderation endpoint to pre-check inputs. Adjust temperature/prompts to reduce edge-case outputs.


## Examples

### Quick Diagnostic Commands
```bash
# Check Wispr status
curl -s https://status.wispr.com

# Verify API connectivity
curl -I https://api.wispr.com

# Check local configuration
env | grep WISPR
```

### Escalation Path
1. Collect evidence with `wispr-debug-bundle`
2. Check Wispr status page
3. Contact support with request ID

## Resources
- [Wispr Status Page](https://status.wispr.com)
- [Wispr Support](https://docs.wispr.com/support)
- [Wispr Error Codes](https://docs.wispr.com/errors)

## Next Steps
For comprehensive debugging, see `wispr-debug-bundle`.