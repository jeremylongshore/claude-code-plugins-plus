---
name: customerio-known-pitfalls
description: |
  Identify and avoid Customer.io anti-patterns.
  Use when reviewing integrations, avoiding common mistakes,
  or optimizing existing Customer.io implementations.
  Trigger with phrases like "customer.io mistakes", "customer.io anti-patterns",
  "customer.io best practices", "customer.io gotchas".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Known Pitfalls

## Overview
Avoid common mistakes and anti-patterns when integrating with Customer.io across authentication, user identification, event tracking, data quality, and performance.

## Prerequisites
- Active Customer.io integration
- Access to codebase with Customer.io calls

## Quick Reference

| Pitfall | Fix |
|---------|-----|
| Wrong API key | Track API for tracking, App API for transactional |
| Milliseconds | Use `Math.floor(Date.now() / 1000)` |
| Track before identify | Always identify first |
| Changing user IDs | Use immutable database IDs |
| No email attribute | Include email for email campaigns |
| Dynamic event names | Use properties instead |
| Blocking requests | Fire-and-forget pattern |
| No bounce handling | Suppress on bounce |
| No rate limiting | Use Bottleneck or similar |
| New client per request | Reuse client singleton |
| Inconsistent event names | Use consistent snake_case |
| PII in event names | Use event data properties |

## Instructions

### Step 1: Review Authentication
Verify you use Track API key for identify/track and App API key for transactional/reporting. Check timestamps use Unix seconds (not milliseconds). Remove any hardcoded credentials.

### Step 2: Audit User Identification
Ensure identify is called before track. Use immutable database IDs (not email). Include `anonymous_id` for merge when transitioning from anonymous to identified.

### Step 3: Check Event Tracking
Standardize on `snake_case` event names. Use event data properties for variations instead of dynamic event names. Use fire-and-forget for non-critical tracking.

### Step 4: Validate Data Quality
Always include email attribute for email campaigns. Keep attribute types consistent. Never put PII in event names or segment names.

### Step 5: Verify Delivery Handling
Handle bounces by suppressing users. Alert on spam complaints immediately. Always include unsubscribe links in email templates.

### Step 6: Optimize Performance
Reuse the TrackClient singleton. Implement rate limiting with Bottleneck. Never block request paths waiting for analytics calls.

For detailed code examples of each pitfall and the anti-pattern audit script, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Solution |
|-------|----------|
| Integration audit fails | Review each category systematically |
| Existing bad data | Run cleanup scripts, re-identify users |
| Performance degradation | Check for per-request client creation |

## Resources
- [Customer.io Best Practices](https://customer.io/docs/best-practices/)
- [Common Issues](https://customer.io/docs/troubleshooting/)

## Next Steps
After reviewing pitfalls, proceed to `customerio-reliability-patterns` for fault tolerance.
