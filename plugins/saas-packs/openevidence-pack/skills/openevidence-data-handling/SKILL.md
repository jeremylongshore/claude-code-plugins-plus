---
name: openevidence-data-handling
description: |
  Implement HIPAA-compliant PHI data handling for OpenEvidence integrations.
  Use when implementing data protection, configuring retention policies,
  or ensuring compliance for clinical AI data flows.
  Trigger with phrases like "openevidence phi", "openevidence data",
  "openevidence hipaa data", "clinical data handling", "patient data protection".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Data Handling

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement HIPAA-compliant Protected Health Information (PHI) handling for OpenEvidence clinical AI integrations. Covers PHI detection, de-identification, encrypted storage, retention policies, and audit trails.

## Prerequisites
- Signed BAA with OpenEvidence
- Understanding of HIPAA regulations
- Data classification policy
- Encryption infrastructure

## HIPAA Data Categories

| Category | Examples | Handling |
|----------|----------|----------|
| PHI Identifiers | Name, DOB, SSN, MRN | Never send to OpenEvidence |
| Clinical Data | Conditions, medications | May send de-identified |
| Query Results | Answers, citations | Cache with encryption, audit access |
| Audit Logs | User actions, timestamps | Retain 6 years, encrypt |

## Instructions

### Step 1: Implement PHI Detection
Create regex patterns for SSN, MRN, phone, email, DOB, dates, names, and addresses. Auto-detect and replace with `[TYPE_REDACTED]` placeholders before any API call.

### Step 2: De-identify Patient Context
Map exact ages to ranges (infant/child/adolescent/young-adult/adult/middle-aged/elderly). Map specific conditions to categories (cardiovascular, metabolic, respiratory). Map medications to drug classes.

### Step 3: Encrypt Cached Data
Use AES-256-GCM encryption for all cached OpenEvidence responses. Store IV + AuthTag + ciphertext. Implement `EncryptedCacheStore` wrapping Redis.

### Step 4: Configure Retention Policies
- Audit logs: 2190 days (6 years, HIPAA minimum), archive after 1 year
- Query cache: 1 day maximum
- DeepConsult reports: 365 days, archive after 90 days
- Error logs: 90 days (no PHI)

### Step 5: Build Audit Trail
Log all PHI access with userId, userRole, action, resourceId, encrypted IP and userAgent. Support filtered queries with pagination for compliance review.

## Output
- PHI detection and auto-sanitization
- Patient context de-identification (age ranges, condition categories, drug classes)
- AES-256-GCM encrypted cache store
- HIPAA-compliant retention policies with archival
- Comprehensive audit trail with encryption

## Error Handling
| Data Issue | Detection | Resolution |
|------------|-----------|------------|
| PHI detected in query | Pattern matching | Auto-sanitize and warn |
| Decryption failure | Cache read error | Delete corrupted entry, re-query |
| Retention job fails | Cron monitoring | Check database permissions, re-run |
| Audit gap | Compliance review | Add middleware to missing routes |

## Examples

### 18 HIPAA Identifiers (Never Send)
Names, geographic data, dates, phone/fax, email, SSN, MRN, health plan numbers, account numbers, certificate/license numbers, vehicle/device identifiers, URLs, IPs, biometrics, photos, other unique characteristics.

### Data Flow
```
User Query -> PHI Detection -> De-identification -> OpenEvidence API
                  |                                       |
             Audit Log (encrypted)               Encrypted Cache
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [OpenEvidence Security](https://www.openevidence.com/security)