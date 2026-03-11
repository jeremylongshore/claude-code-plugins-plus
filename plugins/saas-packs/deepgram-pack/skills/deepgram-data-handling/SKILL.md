---
name: deepgram-data-handling
description: |
  Implement audio data handling best practices for Deepgram integrations.
  Use when managing audio file storage, implementing data retention policies,
  or ensuring GDPR/HIPAA compliance for transcription data.
  Trigger with phrases like "deepgram data", "audio storage", "transcription data",
  "deepgram GDPR", "deepgram HIPAA", "deepgram privacy".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Best practices for handling audio data and transcriptions with Deepgram, including secure upload with encryption, PII redaction, data retention policies, GDPR compliance, and audit logging.

## Prerequisites
- Understanding of data protection regulations
- Cloud storage configured (S3/GCS)
- Encryption capabilities (KMS)
- Data retention policies defined

## Instructions

### Step 1: Implement Secure Upload
Validate audio format (WAV/MP3/FLAC headers), encrypt with AES-256-GCM via KMS data keys, upload to S3 with server-side encryption, and set expiration metadata.

### Step 2: Configure PII Redaction
Apply regex-based redaction for SSN, credit card, phone, email, and date of birth patterns. Also use Deepgram's built-in `redact` option for PCI/SSN/numbers.

### Step 3: Set Up Data Retention
Define policies: standard (30 days), legal hold (7 years), HIPAA (6 years). Auto-enforce retention by scanning S3 objects and deleting expired items in batches.

### Step 4: Implement GDPR Right to Erasure
Process deletion requests by removing transcripts from database, audio files from S3, and user metadata. Log all deletions for audit. Support data export for portability.

### Step 5: Enable Audit Logging
Log all data access events with tamper-evident hashing. Forward to external SIEM if configured.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Secure audio upload with KMS encryption
- PII redaction (regex + Deepgram built-in)
- Automated data retention enforcement
- GDPR erasure and data export
- Tamper-evident audit logging

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid audio format | Wrong file type | Validate magic bytes before upload |
| Encryption failure | KMS unavailable | Retry with backoff, alert ops |
| Retention miss | Cron failure | Monitor retention job, add alerts |
| GDPR incomplete | Partial deletion | Transaction-based deletion with rollback |

## Examples

### Data Lifecycle
```
Upload -> Process -> Store -> Retain -> Archive -> Delete
  |         |         |        |         |          |
Encrypt  Transcribe  Save   Review   Compress   Secure Delete
```

### Compliance Requirements
| Regulation | Key Requirements |
|------------|------------------|
| GDPR | Data minimization, right to deletion, consent |
| HIPAA | PHI protection, access controls, audit logs |
| SOC 2 | Security controls, availability, confidentiality |
| PCI DSS | Data encryption, access logging |

## Resources
- [Deepgram Security](https://deepgram.com/security)
- [GDPR Compliance Guide](https://developers.deepgram.com/docs/gdpr)
- [HIPAA Compliance](https://deepgram.com/hipaa)
