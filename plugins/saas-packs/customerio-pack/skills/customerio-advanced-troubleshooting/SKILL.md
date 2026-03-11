---
name: customerio-advanced-troubleshooting
description: |
  Apply Customer.io advanced debugging techniques.
  Use when diagnosing complex issues, investigating
  delivery problems, or debugging integration failures.
  Trigger with phrases like "debug customer.io", "customer.io investigation",
  "customer.io troubleshoot", "customer.io incident".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Advanced Troubleshooting

## Overview
Advanced debugging techniques for diagnosing complex Customer.io integration issues including API debugging, user investigation, campaign analysis, and incident response.

## Prerequisites
- Access to Customer.io dashboard
- Application logs access
- Understanding of your integration architecture

## Troubleshooting Framework
1. What is the expected behavior?
2. What is the actual behavior?
3. When did the issue start?
4. How many users/messages affected?
5. Is it consistent or intermittent?

## Instructions

### Step 1: API Debugging
Build a debug client wrapper that logs request details, measures latency, and captures error codes and response bodies for every operation.

### Step 2: User Profile Investigation
Create investigation scripts that check profile existence, required attributes (email), suppression status, bounce/complaint history, and recent activity.

### Step 3: Campaign Debugging
Analyze campaign status, trigger conditions, audience size, and recent send activity to find why messages aren't delivering.

### Step 4: Webhook Debugging
Verify webhook signatures, parse payloads, count processed events, and capture per-event errors with timing data.

### Step 5: Network Diagnostics
Run DNS resolution, TCP connectivity, TLS certificate, API latency, and rate limit checks against Customer.io endpoints.

### Step 6: Follow Incident Response Runbook
Apply the appropriate runbook for the priority level: P1 (complete outage), P2 (high error rate), P3 (delivery issues), P4 (webhook failures).

For detailed implementation code and diagnostic scripts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Diagnostic Commands
```bash
# Check API health
curl -s "https://status.customer.io/api/v2/status.json" | jq '.status'
# Test authentication
curl -u "$CIO_SITE_ID:$CIO_API_KEY" "https://track.customer.io/api/v1/accounts"
# Check user exists
curl -u "$CIO_SITE_ID:$CIO_API_KEY" "https://track.customer.io/api/v1/customers/USER_ID"
```

## Error Handling
| Issue | Solution |
|-------|----------|
| User not receiving | Check suppression, segments, attributes |
| Events not tracked | Verify user identified first |
| High latency | Check network, enable connection pooling |

## Resources
- [Customer.io Status](https://status.customer.io/)
- [Troubleshooting Guide](https://customer.io/docs/troubleshooting/)

## Next Steps
After troubleshooting, proceed to `customerio-reliability-patterns` for resilience.
