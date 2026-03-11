---
name: customerio-security-basics
description: |
  Apply Customer.io security best practices.
  Use when implementing secure integrations, handling PII,
  or setting up proper access controls.
  Trigger with phrases like "customer.io security", "customer.io pii",
  "secure customer.io", "customer.io gdpr".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Security Basics

## Overview
Implement security best practices for Customer.io integrations including credential management, PII handling, webhook verification, and GDPR compliance.

## Prerequisites
- Customer.io account with admin access
- Understanding of your data classification
- Environment variable management

## Instructions

### Step 1: Set Up Secure Credential Management
Use a secrets manager (GCP Secret Manager, AWS Secrets Manager) instead of environment variables for production credentials.

### Step 2: Implement PII Data Handling
Hash sensitive identifiers with SHA-256 before sending. Sanitize user attributes to remove highly sensitive fields (SSN, credit card) and optionally hash PII fields (phone, address).

### Step 3: Configure API Key Rotation
Establish a 90-day rotation schedule. Automate through secrets manager where possible with zero-downtime rotation procedures.

### Step 4: Secure Webhook Endpoints
Verify Customer.io webhook signatures using HMAC-SHA256 with `crypto.timingSafeEqual`. Create Express middleware for automatic verification.

### Step 5: Implement Access Controls
Define role-based permissions (admin, editor, viewer) and enable audit logging for security-sensitive operations.

### Step 6: Handle Data Retention
Implement user suppression and deletion for GDPR/CCPA compliance. Create anonymization functions for historical analytics data.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Security Checklist
- [ ] API keys stored in secrets manager
- [ ] API keys rotated every 90 days
- [ ] Webhook signatures verified
- [ ] PII sanitized before sending
- [ ] Minimum necessary data sent
- [ ] Team access follows least-privilege
- [ ] Audit logging enabled
- [ ] GDPR/CCPA deletion process documented
- [ ] SSL/TLS enforced for all API calls

## Error Handling
| Issue | Solution |
|-------|----------|
| Exposed credentials | Rotate immediately, audit access |
| PII leak | Delete from Customer.io, notify DPO |
| Unauthorized access | Review access logs, revoke access |

## Resources
- [Customer.io Security](https://customer.io/security/)
- [GDPR Compliance](https://customer.io/docs/gdpr/)
- [Suppression API](https://customer.io/docs/api/track/#operation/suppress)

## Next Steps
After implementing security, proceed to `customerio-prod-checklist` for production readiness.
