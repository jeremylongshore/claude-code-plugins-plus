---
name: deepgram-security-basics
description: |
  Apply Deepgram security best practices for API key management and data protection.
  Use when securing Deepgram integrations, implementing key rotation,
  or auditing security configurations.
  Trigger with phrases like "deepgram security", "deepgram API key security",
  "secure deepgram", "deepgram key rotation", "deepgram data protection".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Security Basics

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement security best practices for Deepgram API integration including key management, scoped permissions, key rotation, data protection (encryption at rest, PII redaction), and audit logging.

## Prerequisites
- Deepgram Console access
- Understanding of environment variables
- Knowledge of secret management (AWS Secrets Manager or GCP Secret Manager)

## Security Checklist
- [ ] API keys stored in environment variables or secret manager
- [ ] Different keys for development/staging/production
- [ ] Key rotation schedule established (90-day expiry recommended)
- [ ] Scoped API keys with minimal permissions
- [ ] Audit logging enabled
- [ ] Network access restricted (HTTPS only, no private IPs)
- [ ] Transcript data encrypted at rest

## Instructions

### Step 1: Secure API Key Storage
Never hardcode keys. Use `.env` locally (gitignored) and secret managers in cloud environments.

### Step 2: Create Scoped Keys
Create separate keys with minimal permissions: `listen:*` for transcription, `manage:*` for admin, `usage:read` for monitoring.

### Step 3: Implement Key Rotation
Set up 90-day automated rotation: create new key, validate it, update secret manager, schedule old key deletion.

### Step 4: Sanitize Inputs
Validate audio URLs (HTTPS only, block localhost/private IPs). Sanitize transcript responses to allowed fields only.

### Step 5: Encrypt Transcripts at Rest
Use AES-256-GCM for transcript storage encryption. Implement PII redaction for credit cards, SSNs, phone numbers, and emails.

### Step 6: Enable Audit Logging
Log all transcription operations with userId, ipAddress, success status, and duration.

## Output
- Secret manager integration (AWS/GCP)
- Key rotation automation
- Scoped API key configuration
- Request sanitization (URL and response)
- AES-256-GCM encryption/decryption for transcripts
- PII redaction patterns
- Audit logging service

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| 401 after rotation | Old key still cached | Clear key cache, restart services |
| Private IP blocked | SSRF attempt | Validate URL against blocklist |
| Decryption fails | Wrong key or corrupt data | Check encryption key, verify auth tag |
| Audit gaps | Logger misconfigured | Verify audit middleware on all routes |

## Examples

### Environment Setup
```bash
# .env (NEVER commit)
DEEPGRAM_API_KEY=actual-secret-key

# .gitignore
.env
.env.local
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Security Overview](https://deepgram.com/security)
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [HIPAA Compliance](https://deepgram.com/hipaa)
- [SOC 2 Compliance](https://deepgram.com/soc2)
