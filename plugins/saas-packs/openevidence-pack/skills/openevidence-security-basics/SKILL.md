---
name: openevidence-security-basics
description: |
  Apply OpenEvidence security best practices for HIPAA compliance and PHI protection.
  Use when securing API keys, implementing PHI handling,
  or auditing OpenEvidence security configuration.
  Trigger with phrases like "openevidence security", "openevidence hipaa",
  "openevidence phi", "secure openevidence", "openevidence compliance".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Security Basics

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Security best practices for OpenEvidence integrations handling Protected Health Information (PHI). Covers credential management, PHI sanitization, HIPAA audit logging, webhook verification, and data retention compliance.

## Prerequisites
- OpenEvidence SDK installed
- Understanding of HIPAA requirements
- Signed Business Associate Agreement (BAA)
- Access to organization security policies

## OpenEvidence Security Certifications
- SOC 2 Type II certified
- HIPAA compliant with BAA
- AES-256 encryption at rest
- TLS 1.2+ encryption in transit

## Security Checklist
- [ ] API keys in secret manager (not env vars in production)
- [ ] BAA signed with OpenEvidence
- [ ] PHI sanitization before all queries
- [ ] HIPAA audit logging on all access
- [ ] Webhook signatures verified
- [ ] TLS 1.2+ enforced
- [ ] Different keys for dev/staging/prod
- [ ] Key rotation schedule established
- [ ] Data retention policy implemented

## Instructions

### Step 1: Secure Credential Management
Use `.env` locally (gitignored), GCP Secret Manager or AWS Secrets Manager in production. Never hardcode credentials.

### Step 2: Implement PHI Sanitization
Remove names, dates, MRNs, SSNs from queries before sending to OpenEvidence. Map patient demographics to age ranges and condition categories instead of specific identifiers.

### Step 3: Enable HIPAA Audit Logging
Log all clinical queries and DeepConsult requests with userId, userRole, resourceId, ipAddress, success status. Never log actual query content or responses (may contain PHI).

### Step 4: Verify Webhook Signatures
Parse `t=timestamp,v1=signature` header format. Compute HMAC-SHA256 with timing-safe comparison. Reject timestamps older than 5 minutes for replay protection.

### Step 5: Configure Data Retention
- Audit logs: 6 years (2190 days) -- HIPAA minimum
- Query results: Do not store (re-query as needed)
- DeepConsult reports: 1 year
- Run daily cleanup job to enforce policies

## Output
- Secure credential management (GCP/AWS Secret Manager)
- PHI sanitization layer with pattern detection
- HIPAA-compliant audit logging
- Webhook signature verification with replay protection
- Data retention compliance with automated cleanup

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key | Git scanning alert | Rotate immediately, audit access |
| PHI in query | Log pattern matching | Block request, alert compliance |
| Failed signature | Webhook verification | Reject webhook, alert security |
| Unauthorized access | Audit log review | Revoke access, investigate |

## Examples

### Secure Query Flow
```typescript
const sanitized = sanitizeQueryForOpenEvidence(question, patientContext);
const response = await client.query({ question: sanitized.question, context: sanitized.context });
await auditLogger.logClinicalQuery(user.id, user.role, response.id, true, request);
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence Security](https://www.openevidence.com/security)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)