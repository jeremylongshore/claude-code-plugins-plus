---
name: langfuse-common-errors
description: |
  Diagnose and fix Langfuse common errors and exceptions.
  Use when encountering Langfuse errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "langfuse error", "fix langfuse",
  "langfuse not working", "debug langfuse".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langfuse]
---

# Langfuse Common Errors

## Overview

Quick reference for the most common Langfuse API errors: authentication failures, rate limits, context length issues, and model availability.


## Prerequisites
- Langfuse SDK installed
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
# Check Langfuse status
curl -s https://status.langfuse.com

# Verify API connectivity
curl -I https://api.langfuse.com

# Check local configuration
env | grep LANGFUSE
```

### Escalation Path
1. Collect evidence with `langfuse-debug-bundle`
2. Check Langfuse status page
3. Contact support with request ID

## Resources
- [Langfuse Status Page](https://status.langfuse.com)
- [Langfuse Support](https://docs.langfuse.com/support)
- [Langfuse Error Codes](https://docs.langfuse.com/errors)

## Next Steps
For comprehensive debugging, see `langfuse-debug-bundle`.