---
name: hex-security-basics
description: |
  Apply Hex security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Hex security configuration.
  Trigger with phrases like "hex security", "hex secrets",
  "secure hex", "hex API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Security Basics

## Token Management

| Credential | Scope | Best Practice |
|-----------|-------|---------------|
| API Token (read) | List projects, check status | Use for monitoring |
| API Token (run) | Trigger runs + all read | Use for orchestration only |

## Instructions

### Least Privilege
- Monitoring services: read-only token
- Orchestration services: run token
- Set token expiration (90 days recommended)

### Security Checklist
- [ ] API tokens in secrets vault
- [ ] Token expiration set
- [ ] Separate tokens per environment
- [ ] Pre-commit hook blocks `hex_token_*` leaks
- [ ] Tokens never logged

## Resources

- [Hex API Authentication](https://learn.hex.tech/docs/api/api-overview)
