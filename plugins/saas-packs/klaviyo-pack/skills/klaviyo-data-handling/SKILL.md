---
name: klaviyo-data-handling
description: 'Implement Klaviyo data privacy, GDPR/CCPA compliance, and PII handling
  patterns.

  Use when handling profile data, implementing right-to-deletion, configuring

  data retention, or ensuring compliance with privacy regulations.

  Trigger with phrases like "klaviyo data", "klaviyo PII",

  "klaviyo GDPR", "klaviyo data retention", "klaviyo privacy", "klaviyo CCPA",

  "klaviyo delete profile", "klaviyo data privacy".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Data Handling

## Overview

Handle profile data, PII, and privacy compliance with Klaviyo's Data Privacy API, GDPR right-to-deletion, CCPA requests, and safe logging patterns. This skill covers five workflows: GDPR profile deletion, Data Subject Access Requests (DSAR), PII redaction in logs, consent management, and compliance audit logging.

The GDPR deletion skeleton is inline below. The deeper step-by-step code — DSAR export, PII redaction, consent management, and audit logging — lives in [references/implementation.md](references/implementation.md) so this file stays scannable. Read the summary here, then drill into the reference for full copy-ready code.

## Prerequisites

- `klaviyo-api` SDK installed
- API key with `data-privacy:write` scope (for deletion requests)
- Understanding of GDPR/CCPA requirements
- Audit logging infrastructure

## Klaviyo Data Privacy API

Klaviyo provides a dedicated **Data Privacy API** for GDPR/CCPA profile deletion. When you delete a profile via this API, Klaviyo performs a full GDPR erasure — the profile is permanently removed and cannot be recovered.

## Instructions

The workflow has five steps. Step 1 (deletion) is shown in full here because it is the highest-risk, most-requested operation. Steps 2–5 follow the same session pattern and are fully implemented in [references/implementation.md](references/implementation.md).

### Step 1: GDPR Profile Deletion (Right to Erasure)

Request deletion with **exactly one** identifier (email, phone, or profile ID). Providing more than one returns an error. Deletion is irreversible, so always audit-log the request.

```typescript
import { ApiKeySession, DataPrivacyApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const dataPrivacyApi = new DataPrivacyApi(session);

async function requestProfileDeletion(email: string): Promise<void> {
  await dataPrivacyApi.requestProfileDeletion({
    data: {
      type: 'data-privacy-deletion-job',
      attributes: {
        profile: { data: { type: 'profile', attributes: { email } } },
      },
    },
  });

  await auditLog({
    action: 'GDPR_DELETION_REQUESTED',
    identifier: email,
    service: 'klaviyo',
    timestamp: new Date().toISOString(),
  });
}

await requestProfileDeletion('user-wants-deletion@example.com');
```

The multi-identifier form (email / phone / profile ID with validation) is in [references/implementation.md § Step 1](references/implementation.md).

### Step 2: Data Subject Access Request (DSAR)

Export every profile attribute, event, and list membership for a subject (GDPR Article 15) using `ProfilesApi` + `EventsApi`. Full `exportProfileData()` in [references/implementation.md § Step 2](references/implementation.md).

### Step 3: PII Detection and Redaction in Logs

Wrap every log of a Klaviyo response with `redactPII()` / `redactObject()` so emails, phone numbers, and API keys never land in plaintext logs. Full patterns in [references/implementation.md § Step 3](references/implementation.md).

### Step 4: Consent Management

Record marketing consent with a `consentTimestamp` on every subscribe call, and audit-log the source. Full `recordConsent()` in [references/implementation.md § Step 4](references/implementation.md).

### Step 5: Audit Logging

Persist every privacy action to a retained audit store (7-year retention per GDPR). Full `auditLog()` and schema in [references/implementation.md § Step 5](references/implementation.md).

## Output

Applying this skill produces:

- A `requestProfileDeletion()` call that submits an irreversible GDPR erasure job to Klaviyo and writes a `GDPR_DELETION_REQUESTED` audit entry.
- A DSAR export object containing the subject's profile attributes, event history, and list memberships (GDPR Article 15 response payload).
- Log output with PII replaced by `[REDACTED:type]` markers, e.g. `Profile data: { email: 'joh***' }`.
- Consent records carrying an ISO-8601 `consentTimestamp` plus a matching `CONSENT_RECORDED` audit entry.
- Audit entries retained for 7 years, each carrying `action`, `identifier`, `service`, and `timestamp`.

## Data Classification for Klaviyo

| Data Category | Examples in Klaviyo | Handling |
|--------------|---------------------|----------|
| PII | email, phoneNumber, firstName, lastName | Redact in logs, encrypt at rest |
| Sensitive | API keys, webhook secrets | Never log, rotate quarterly |
| Behavioral | Events, page views, purchases | Anonymize where possible |
| Marketing | List memberships, consent status | Audit trail required |
| Derived | Segments, predictive analytics | No special handling |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Deletion request fails | Missing `data-privacy:write` scope | Update API key scopes |
| Multiple identifiers error | Providing email AND phone | Use exactly one identifier |
| Profile not found for DSAR | Wrong email or already deleted | Search by ID or phone instead |
| PII in error logs | Unredacted API responses | Wrap logger with `redactObject()` |

## Examples

**Delete a profile on a right-to-be-forgotten request:**

```typescript
await requestProfileDeletion('user-wants-deletion@example.com');
// → GDPR erasure job submitted; GDPR_DELETION_REQUESTED audit entry written
```

**Export a subject's data for a DSAR** (see [references/implementation.md § Step 2](references/implementation.md)):

```typescript
const bundle = await exportProfileData('subject@example.com');
// → { profile: {...}, events: [...], lists: [...] }
```

**Redact PII before logging an API response** (see [references/implementation.md § Step 3](references/implementation.md)):

```typescript
console.log('Profile data:', redactObject(profile.attributes));
// → Profile data: { email: 'joh***', firstName: 'Jan***' }
```

Full, copy-ready versions of every example live in [references/implementation.md](references/implementation.md).

## Resources

- [Data Privacy API](https://developers.klaviyo.com/en/reference/data_privacy_api_overview)
- [Request Profile Deletion](https://developers.klaviyo.com/en/reference/request_profile_deletion)
- [Consent Collection Guide](https://developers.klaviyo.com/en/docs/collect_email_and_sms_consent_via_api)
- [Full implementation walkthrough](references/implementation.md) — DSAR, PII redaction, consent, audit logging
- For enterprise access control, see the `klaviyo-enterprise-rbac` skill.
