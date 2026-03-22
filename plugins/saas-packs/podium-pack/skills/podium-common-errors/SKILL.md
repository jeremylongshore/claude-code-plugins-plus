---
name: podium-common-errors
description: |
  Diagnose and fix Podium common errors and exceptions.
  Use when encountering Podium errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "podium error", "fix podium",
  "podium not working", "debug podium".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, podium]
---

# Podium Common Errors

## Overview

Quick reference for the most common Podium errors: delivery failures, suppressed recipients, domain verification, and template issues.


## Prerequisites
- Podium SDK installed
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

### Suppressed Recipient
**Error Message:**
```
422 Unprocessable: Recipient is on suppression list (hard bounce)
```

**Cause:** Recipient previously hard-bounced, unsubscribed, or marked message as spam.

**Solution:**
```bash
# Check suppression status before sending
const status = await client.suppression.check('user@example.com');
# Remove from suppression only if they re-opted in
# Never send to hard-bounced addresses — damages sender reputation

```

---

### Sender Domain Not Verified
**Error Message:**
```
403 Forbidden: Sending domain not verified — add DKIM/SPF records
```

**Cause:** Email sending domain lacks required DNS authentication records.

**Solution:**
# Add DNS records at your registrar:
# SPF: TXT "v=spf1 include:vendor.com ~all"
# DKIM: CNAME selector._domainkey.example.com → dkim.vendor.com
# DMARC: TXT "v=DMARC1; p=quarantine"
# Verify in dashboard after DNS propagation


---

### Template Variable Missing
**Error Message:**
```
400 Bad Request: Template variable {{first_name}} has no value
```

**Cause:** Email template references a variable not provided in the send payload.

**Solution:**
```typescript
# Use default values in templates: {{first_name | default: "there"}}
# Validate payload against template variables before sending
# Check for typos in variable names

```



## Examples

### Quick Diagnostic Commands
```bash
# Check Podium status
curl -s https://status.podium.com

# Verify API connectivity
curl -I https://api.podium.com

# Check local configuration
env | grep PODIUM
```

### Escalation Path
1. Collect evidence with `podium-debug-bundle`
2. Check Podium status page
3. Contact support with request ID

## Resources
- [Podium Status Page](https://status.podium.com)
- [Podium Support](https://docs.podium.com/support)
- [Podium Error Codes](https://docs.podium.com/errors)

## Next Steps
For comprehensive debugging, see `podium-debug-bundle`.