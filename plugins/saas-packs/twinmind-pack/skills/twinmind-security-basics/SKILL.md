---
name: twinmind-security-basics
description: |
  Implement security best practices for TwinMind integrations.
  Use when securing API keys, configuring privacy settings,
  or implementing data protection for meeting recordings.
  Trigger with phrases like "twinmind security", "secure twinmind",
  "twinmind privacy", "protect twinmind data", "twinmind api key security".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Security Basics

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Essential security practices for TwinMind integrations covering API key management, webhook verification, data encryption, access control, privacy configuration, and audit logging.

## Prerequisites
- TwinMind account configured
- Understanding of environment variables
- Basic security and cryptography concepts

## Instructions

### Step 1: Secure API Key Management
Store keys in environment variables or a secrets manager (GCP Secret Manager, AWS Secrets Manager). Never hardcode credentials. Use `.env` files (gitignored) with `.env.example` templates committed to the repo.

### Step 2: Validate Webhook Signatures
Verify `x-twinmind-signature` headers using HMAC-SHA256 with `crypto.timingSafeEqual` to prevent timing attacks. Reject requests with missing or invalid signatures.

### Step 3: Encrypt Sensitive Data at Rest
Use AES-256-GCM encryption for storing transcripts. Store IV and auth tag alongside ciphertext. Key management via environment variables or KMS.

### Step 4: Implement Access Control
Define `Permission` enums (transcripts:read, transcripts:write, settings:manage, admin:*) and Express middleware (`requirePermission`) to enforce RBAC on all routes.

### Step 5: Configure Privacy Settings
Create a `PrivacyConfig` interface controlling audio storage (default: never stored), transcript retention days, encryption, local processing, PII redaction patterns (SSN, credit card, email).

### Step 6: Enable Audit Logging
Build an `AuditLogger` class that records userId, action, resource, timestamp, IP address, and user agent for all sensitive operations. Persist to a logging service.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete security code including encryption, webhook verification, RBAC middleware, and audit logging.

## Output
- Secure API key storage
- Webhook signature verification
- Data encryption at rest
- Access control implementation
- Privacy configuration
- Audit logging

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| API key exposed | Hardcoded secret | Rotate key immediately, audit logs |
| Webhook unverified | Missing middleware | Always verify signatures |
| PII leaked | Missing redaction | Enable PII patterns, encrypt data |
| Unauthorized access | No RBAC | Implement permission middleware |

## Examples
```typescript
// Verify webhook signature
const isValid = verifyWebhookSignature(payload, signature, secret);

// Encrypt transcript
const encrypted = encrypt(transcript, key); // "iv:tag:ciphertext"

// Check permission
app.get('/api/transcripts', requirePermission(Permission.READ_TRANSCRIPTS), handler);
```

## Resources
- [TwinMind Security Whitepaper](https://twinmind.com/security)
- [TwinMind Privacy Policy](https://twinmind.com/privacy)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

## Next Steps
For production deployment, see `twinmind-prod-checklist`.
