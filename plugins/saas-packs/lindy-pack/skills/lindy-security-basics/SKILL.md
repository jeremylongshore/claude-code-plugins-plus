---
name: lindy-security-basics
description: |
  Implement security best practices for Lindy AI integrations.
  Use when securing API keys, configuring permissions,
  or implementing security controls.
  Trigger with phrases like "lindy security", "secure lindy",
  "lindy API key security", "lindy permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Security Basics

## Overview
Security practices for Lindy AI agent integrations. Lindy creates autonomous AI agents that can access external services, execute actions, and handle data -- making security boundaries and permission controls essential.

## Prerequisites
- Lindy account with API access
- Understanding of Lindy's agent execution model
- Awareness of connected service permissions

## Instructions

### Step 1: API Key Protection

### Step 2: Agent Permission Boundaries

Lindy agents can connect to external services. Limit what each agent can access.

### Step 3: Webhook Signature Verification

### Step 4: Audit Agent Actions

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

Log all agent actions for security review and debugging.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent accesses wrong service | No permission boundaries | Define explicit agent permissions |
| Fake webhook processed | No signature verification | Verify HMAC signatures |
| Key exposure | Hardcoded in source | Use environment variables |
| Runaway agent | No action limits | Set per-hour action quotas |

## Examples

### Permission Check Middleware
## Resources
- [Lindy API Docs](https://docs.lindy.ai)
- [Lindy Security](https://www.lindy.ai/security)
