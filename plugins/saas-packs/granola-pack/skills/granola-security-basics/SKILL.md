---
name: granola-security-basics
description: |
  Security and privacy configuration for Granola meeting data.
  Use when reviewing data handling practices, configuring encryption,
  ensuring SOC 2/GDPR compliance, or securing meeting recordings.
  Trigger: "granola security", "granola privacy", "granola encryption",
  "granola SOC 2", "granola GDPR", "secure granola".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, security, compliance, privacy]

---
# Granola Security Basics

## Overview
Granola achieved SOC 2 Type 2 certification in July 2025. It encrypts data with AES-256 at rest and TLS 1.3 in transit. Audio is transcribed server-side and not stored after processing. This skill covers security configuration, compliance posture, and organizational controls.

## Prerequisites
- Granola Business or Enterprise plan (for admin/security controls)
- Understanding of your organization's compliance requirements
- Admin access for workspace-level settings

## Instructions

### Step 1 — Understand Granola's Data Architecture

```
Audio Capture (your device)
  │
  ├─→ Transmitted via TLS 1.3
  │
  ▼
Granola Cloud (transcription)
  │
  ├─→ Transcript generated (GPT-4o / Claude)
  ├─→ Audio DELETED after processing (not stored)
  │
  ▼
Encrypted Storage (AES-256 at rest)
  │
  ├─→ Meeting notes (your typed + AI enhanced)
  ├─→ Transcript text (stored, searchable)
  ├─→ Attendee metadata
  │
  ▼
Your Device (local cache: cache-v3.json)
```

**Key security properties:**
- No bot joins your meeting — audio is captured locally via system audio
- Raw audio is **never stored** after transcription
- Granola does **not** allow OpenAI or Anthropic to train on customer data
- Enterprise plan enforces org-wide AI training opt-out by default
- Local cache (`cache-v3.json`) contains meeting data on your device

### Step 2 — Configure Account Security

| Control | How to Enable | Plan Required |
|---------|--------------|---------------|
| Google/Microsoft SSO | Default (social login) | All |
| Enterprise SSO (Okta, Azure AD) | Settings > Security > SSO | Enterprise |
| SCIM provisioning | Settings > Security > SCIM | Enterprise |
| Session timeout | Settings > Security | Enterprise |
| IP allowlisting | Contact Granola support | Enterprise |

### Step 3 — Configure Data Controls

**Sharing defaults:**
```
Settings > Privacy:
  Default sharing: Private (recommended)
  Auto-share with attendees: Off (enable per-folder instead)
  External sharing: Disabled or Admin Approval Required
  Public links: Disabled
  Link expiration: 30 days (if external sharing enabled)
```

**Data retention:**
```
Settings > Data Retention:
  Meeting notes: Organization policy (1-2 years typical)
  Transcripts: 90 days (recommended for storage efficiency)
  Audio: Deleted after processing (Granola default, not configurable)
```

**AI training opt-out:**
```
Settings > Privacy > AI Training:
  Organization-wide opt-out: Enabled (Enterprise: enforced by default)
```
This ensures your meeting data is never used to train foundational models.

### Step 4 — Meeting Recording Consent

Granola records audio from your device. You are responsible for informing meeting participants:

**Legal requirements by jurisdiction:**
- **One-party consent** (US federal, most US states, UK): You can record if you are a participant
- **Two-party/all-party consent** (California, Illinois, EU GDPR): All participants must be informed
- **Always recommended:** Announce recording at meeting start or include notice in calendar invites

**Calendar invite consent notice:**
```
Note: This meeting will be recorded using Granola AI for note-taking
purposes. By joining, you consent to the recording and AI processing
of the discussion. Contact [your-email] to opt out.
```

### Step 5 — Compliance Posture

| Framework | Granola Status | Evidence |
|-----------|---------------|----------|
| SOC 2 Type 2 | Certified (July 2025) | Available on request |
| GDPR | Compliant | DPA available |
| CCPA | Compliant | Privacy policy updated |
| HIPAA | Not certified | Do not use for PHI without BAA |
| ISO 27001 | Not certified | Covered by SOC 2 controls |

**GDPR requirements you must implement:**
- Right of Access: Export user's data via Settings > Data > Export
- Right to Erasure: Delete user's notes and request account deletion
- Data Processing Agreement: Request DPA from Granola (required for EU data)
- Subject Access Requests: 30-day response deadline

### Step 6 — Sensitive Meeting Protocol

For confidential meetings (board discussions, HR, legal, M&A):

1. **Before:** Disable auto-recording for the meeting
2. **During:** Announce recording consent to all participants
3. **After:** Review and redact sensitive content before sharing
4. **Sharing:** Set link expiration, restrict to named recipients
5. **Retention:** Apply shorter retention (30 days) for sensitive workspaces

## Output
- Account secured with SSO and appropriate authentication
- Sharing defaults configured per organizational policy
- Data retention policies set per data type
- Compliance posture documented and gaps identified
- Sensitive meeting protocol established

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| SSO login fails | SAML/OIDC misconfigured | Verify Entity ID and ACS URL with IdP |
| Cannot disable external sharing | Individual override | Set workspace-level policy to override user settings |
| Data export fails | Insufficient permissions | Request export access from workspace admin |
| Consent notice ignored | Not in calendar template | Add to organization's default calendar template |

## Local Cache Security
The local cache file (`~/Library/Application Support/Granola/cache-v3.json`) contains meeting data in plaintext. For sensitive environments:
- Enable FileVault (macOS) or BitLocker (Windows) for disk encryption
- Restrict file permissions: `chmod 600 "$HOME/Library/Application Support/Granola/cache-v3.json"`
- Be aware that MCP servers and local scripts can read this file

## Resources
- [Granola Security Page](https://www.granola.ai/security)
- [Security Standards (Docs)](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)
- [Privacy & Data FAQs](https://docs.granola.ai/help-center/consent-security-privacy/security-privacy-data-faqs)
- [Data Processing Addendum](https://help.granola.ai/article/data-processing-addendum)

## Next Steps
Proceed to `granola-prod-checklist` for production rollout preparation.
