---
name: customerio-debug-bundle
description: |
  Collect Customer.io debug evidence for support.
  Use when creating support tickets, reporting issues,
  or documenting integration problems.
  Trigger with phrases like "customer.io debug", "customer.io support ticket",
  "collect customer.io logs", "customer.io diagnostics".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive debug information for Customer.io support tickets and troubleshooting.

## Prerequisites
- Customer.io API credentials
- Access to application logs
- User ID or email of affected user

## Instructions

### Step 1: Create Debug Script
### Step 2: Collect User-Specific Data
### Step 3: Collect Application Logs
### Step 4: Generate Support Report
### Step 5: Bundle and Submit

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Debug script for API testing
- User-specific diagnostic data
- Application log collection
- Support report template
- Compressed debug bundle

## Error Handling
| Issue | Solution |
|-------|----------|
| Logs too large | Use `tail -n 1000` to limit |
| Sensitive data | Use redaction script |
| Missing permissions | Check file read access |

## Resources
- [Customer.io Support](https://customer.io/contact/)
- [API Status](https://status.customer.io/)

## Next Steps
After creating debug bundle, proceed to `customerio-rate-limits` to understand API limits.

## Examples

**Basic usage**: Apply customerio debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio debug bundle for production environments with multiple constraints and team-specific requirements.