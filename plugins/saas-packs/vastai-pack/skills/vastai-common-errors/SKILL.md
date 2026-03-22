---
name: vastai-common-errors
description: |
  Diagnose and fix Vast.ai common errors and exceptions.
  Use when encountering Vast.ai errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "vastai error", "fix vastai",
  "vastai not working", "debug vastai".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, vastai]
---

# Vast.ai Common Errors

## Overview

Quick reference for the top 10 most common Vast.ai errors and their solutions.


## Prerequisites
- Vast.ai SDK installed
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
# Check Vast.ai status
curl -s https://status.vastai.com

# Verify API connectivity
curl -I https://api.vastai.com

# Check local configuration
env | grep VASTAI
```

### Escalation Path
1. Collect evidence with `vastai-debug-bundle`
2. Check Vast.ai status page
3. Contact support with request ID

## Resources
- [Vast.ai Status Page](https://status.vastai.com)
- [Vast.ai Support](https://docs.vastai.com/support)
- [Vast.ai Error Codes](https://docs.vastai.com/errors)

## Next Steps
For comprehensive debugging, see `vastai-debug-bundle`.