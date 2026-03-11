---
name: gamma-data-handling
description: |
  Handle data privacy, retention, and compliance for Gamma integrations.
  Use when implementing GDPR compliance, data retention policies,
  or managing user data within Gamma workflows.
  Trigger with phrases like "gamma data", "gamma privacy",
  "gamma GDPR", "gamma data retention", "gamma compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement proper data handling, privacy controls, and GDPR/CCPA compliance for Gamma integrations.

## Prerequisites
- Understanding of data privacy regulations (GDPR, CCPA)
- Data classification policies defined
- Legal/compliance team consultation

## Data Classification

| Type | Classification | Retention | Handling |
|------|----------------|-----------|----------|
| Presentation content | User data | User-controlled | Encrypted at rest |
| AI-generated text | Derived data | With source | Standard |
| User prompts | PII potential | 30 days | Anonymize logs |
| Export files | User data | 24 hours cache | Auto-delete |

## Instructions

### Step 1: Implement Consent Management
Check user consent before Gamma operations. Require explicit consent for data processing and AI analysis separately.

### Step 2: Configure PII Handling
Mask emails, hash names, and remove sensitive fields before logging. Never log raw PII in production.

### Step 3: Enforce Retention Policies
Auto-delete exports (1 day), anonymize prompts (30 days), archive logs (90 days), delete presentations (365 days). Schedule daily enforcement.

### Step 4: Handle GDPR Requests
- **Access**: Gather all user data including Gamma-stored presentations
- **Erasure**: Delete from local DB and Gamma API, anonymize user record

### Step 5: Enable Audit Trail
Log all significant actions (create, update, delete, share, export) with user ID, IP, timestamp, and resource details.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for consent management, PII sanitization, retention enforcement, GDPR request handlers, and audit trail code.

## Output
- Consent management enforced before operations
- PII sanitized in all logs
- Retention policies running daily
- GDPR access/erasure requests handled
- Audit trail recording all actions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Consent not obtained | New user flow | Add consent gate before first operation |
| Deletion incomplete | Gamma API timeout | Retry with exponential backoff |
| Audit gap | Missing log entry | Add audit middleware to all routes |
| Retention not running | Scheduler stopped | Monitor cron job health |

## Examples

### Compliance Checklist
- [ ] Data processing agreement with Gamma signed
- [ ] User consent mechanism implemented
- [ ] PII handling procedures documented
- [ ] Data retention policies enforced
- [ ] GDPR rights request process ready
- [ ] Audit logging enabled

## Resources
- [Gamma Privacy Policy](https://gamma.app/privacy)
- [Gamma DPA](https://gamma.app/dpa)
- [GDPR Compliance Guide](https://gdpr.eu/)

## Next Steps
Proceed to `gamma-enterprise-rbac` for access control.