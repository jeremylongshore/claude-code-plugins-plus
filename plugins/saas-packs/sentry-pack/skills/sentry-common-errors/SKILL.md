---
name: sentry-common-errors
description: |
  Diagnose and fix Sentry common errors and exceptions.
  Use when encountering Sentry errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "sentry error", "fix sentry",
  "sentry not working", "debug sentry".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry Common Errors

## Overview

Quick reference for the top 10 most common Sentry errors and their solutions.


## Prerequisites
- Sentry SDK installed
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

### Event Quota Exceeded
**Error Message:**
```
429 Event Dropped: Monthly quota of 100,000 events exceeded
```

**Cause:** Exceeded monthly event ingestion limit. Events are silently dropped.

**Solution:**
```bash
# Check current usage in billing dashboard
# Reduce sample rate for high-volume events
# Set up spike protection: client.init({ maxBreadcrumbs: 50 })
# Upgrade plan or purchase additional quota

```

---

### Instance Capacity Unavailable
**Error Message:**
```
503 Service Unavailable: No capacity for gpu.a100 in us-east-1
```

**Cause:** Requested GPU/compute type is fully allocated in the target region.

**Solution:**
# Try alternative regions or instance types
# Use spot/preemptible instances if workload tolerates interruption
# Set up capacity reservation for guaranteed availability
# Enable multi-region fallback in provisioning logic


---

### Agent Connection Lost
**Error Message:**
```
Warning: Agent heartbeat missed for host web-prod-3 (last seen 5m ago)
```

**Cause:** Monitoring agent on the host stopped reporting. Host may be down or network issue.

**Solution:**
```typescript
# SSH into host and check agent status
systemctl status monitoring-agent
# Check agent logs for errors
journalctl -u monitoring-agent --since "10 minutes ago"
# Restart agent if process died
systemctl restart monitoring-agent

```



## Examples

### Quick Diagnostic Commands
```bash
# Check Sentry status
curl -s https://status.sentry.com

# Verify API connectivity
curl -I https://api.sentry.com

# Check local configuration
env | grep SENTRY
```

### Escalation Path
1. Collect evidence with `sentry-debug-bundle`
2. Check Sentry status page
3. Contact support with request ID

## Resources
- [Sentry Status Page](https://status.sentry.com)
- [Sentry Support](https://docs.sentry.com/support)
- [Sentry Error Codes](https://docs.sentry.com/errors)

## Next Steps
For comprehensive debugging, see `sentry-debug-bundle`.