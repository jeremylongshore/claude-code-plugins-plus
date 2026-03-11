---
name: twinmind-data-handling
description: |
  Handle data privacy, GDPR compliance, and data retention for TwinMind.
  Use when implementing data protection, handling user data requests,
  or ensuring compliance with privacy regulations.
  Trigger with phrases like "twinmind GDPR", "twinmind data privacy",
  "twinmind data retention", "twinmind user data", "twinmind compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Data privacy, retention, and compliance procedures for TwinMind meeting transcriptions including PII redaction, GDPR data subject requests, consent management, and data anonymization.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- TwinMind account with admin access
- Database access for data management
- Legal/compliance team consultation

## Instructions

### Step 1: Configure Data Retention Policies
Define `RetentionPolicy` with configurable retention days for transcripts (default 90), summaries (linked to transcript), action items (180 days), and user profiles (30 days post-deletion). Implement auto-cleanup job for expired data.

### Step 2: Implement PII Redaction
Build PII detection with regex patterns for SSN, credit card, email, phone, and IP address. Create `redactPII()` function returning redacted text and a count of redactions by type. Enable automatic redaction via TwinMind settings API.

### Step 3: Handle GDPR Data Subject Requests
Implement `GDPRHandler` with right to access (Article 15), right to erasure (Article 17), and right to data portability (Article 20). Track DSR requests with 30-day deadline and compliance team notifications.

### Step 4: Manage Consent
Build `ConsentManager` tracking consent per purpose (transcription, aiProcessing, storage, sharing, marketing). Add Express middleware `requireConsent()` that blocks processing without valid consent.

### Step 5: Data Anonymization
Implement transcript anonymization using HMAC-based ID hashing, PII redaction, and speaker name replacement for analytics exports.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete retention policy, PII patterns, GDPR handlers, consent manager, and anonymization code.

## Output
- Data retention policy configuration
- PII redaction implementation
- GDPR request handlers
- Consent management system
- Data anonymization utilities

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| DSR deadline missed | Processing delay | Automate DSR handling |
| PII not redacted | Pattern not matched | Update regex patterns |
| Consent invalid | Version mismatch | Re-request consent |
| Data not deleted | Cascade failure | Verify deletion recursively |

## Examples
```typescript
// Redact PII from transcript
const { redactedText, redactions } = redactPII("Contact john@example.com");
// redactedText: "Contact [EMAIL REDACTED]"
// redactions: [{ type: 'Email', count: 1 }]

// Handle GDPR erasure request
const gdpr = new GDPRHandler();
const result = await gdpr.handleErasureRequest('user@example.com');
console.log(`Deleted ${result.transcriptsDeleted} transcripts`);
```

## TwinMind Privacy Features
- **No audio storage**: Audio processed in real-time and immediately deleted
- **On-device processing**: Option for local transcription
- **Encrypted storage**: Transcripts encrypted with user-controlled keys
- **Data residency**: Choose storage region (EU, US, APAC)

## Resources
- [GDPR Official Text](https://gdpr.eu/)
- [TwinMind Privacy Policy](https://twinmind.com/privacy)
- [TwinMind DPA Template](https://twinmind.com/legal/dpa)

## Next Steps
For enterprise access control, see `twinmind-enterprise-rbac`.
