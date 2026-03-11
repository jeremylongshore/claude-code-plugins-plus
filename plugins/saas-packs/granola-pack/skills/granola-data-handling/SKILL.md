---
name: granola-data-handling
description: |
  Data export, retention, and GDPR compliance for Granola.
  Use when managing data exports, configuring retention policies,
  or ensuring regulatory compliance.
  Trigger with phrases like "granola export", "granola data",
  "granola GDPR", "granola retention", "granola compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Manage data export, retention policies, and GDPR/CCPA compliance for Granola meeting data.

## Prerequisites
- Granola admin access
- Understanding of data regulations (GDPR, CCPA)
- Export destination prepared

## Data Classification

| Data Type | Sensitivity | Retention | Export Format |
|-----------|-------------|-----------|---------------|
| Meeting Notes | Medium | Configurable | Markdown, JSON |
| Transcripts | High | Configurable | Text, JSON |
| Audio | High | Short-term | WAV, MP3 |
| Attendee Info | PII | With notes | JSON |

## Instructions

### Step 1: Configure Data Export
- Single meeting: Open > ... menu > Export (Markdown/PDF/JSON)
- Bulk export: Settings > Data > Export > Select date range > JSON format

### Step 2: Set Retention Policies
Configure per data type: notes (1-2 years), transcripts (90 days), audio (delete after processing). Apply workspace-specific overrides for HR/Sales/Engineering.

### Step 3: Implement GDPR Compliance
- Enable self-service data export (Right of Access)
- Document SAR handling process (30-day response deadline)
- Implement deletion workflow for Right to Be Forgotten
- Sign DPA with Granola, update privacy policy

### Step 4: Add Meeting Recording Notice
Include consent notice in meeting invites for CCPA/GDPR compliance.

### Step 5: Set Up Archival
Monthly export of notes > 6 months old to cloud storage (GCS/S3), verify integrity, delete from Granola.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for export format examples, retention policy templates, GDPR/CCPA procedures, security controls, and archival strategy.

## Output
- Export procedures documented and tested
- Retention policies configured per workspace
- GDPR/CCPA compliance implemented
- Archival workflow automated

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Export incomplete | Large dataset | Use bulk export with date range filters |
| Deletion not propagated | Backup retention | Allow 30 days for backup purge |
| SAR deadline missed | No process owner | Assign dedicated compliance contact |
| Consent not captured | Missing notice | Add recording notice to calendar templates |

## Examples

### Recommended Retention by Type
| Data Type | Recommendation | Reason |
|-----------|---------------|--------|
| Notes | 1-2 years | Reference value |
| Transcripts | 90 days | Storage efficiency |
| Audio | Delete after processing | Privacy, storage |

## Resources
- [Granola Privacy Policy](https://granola.ai/privacy)
- [Granola Security](https://granola.ai/security)
- [GDPR Documentation](https://granola.ai/gdpr)

## Next Steps
Proceed to `granola-enterprise-rbac` for role-based access control.