---
name: klaviyo-data-handling
description: |
  Implement Klaviyo data privacy, GDPR/CCPA compliance, and PII handling patterns.
  Use when handling profile data, implementing right-to-deletion, configuring
  data retention, or ensuring compliance with privacy regulations.
  Trigger with phrases like "klaviyo data", "klaviyo PII",
  "klaviyo GDPR", "klaviyo data retention", "klaviyo privacy", "klaviyo CCPA",
  "klaviyo delete profile", "klaviyo data privacy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Data Handling

## Overview

Handle profile data, PII, and privacy compliance with Klaviyo's Data Privacy API, GDPR right-to-deletion, CCPA requests, and safe logging patterns.

## Prerequisites

- `klaviyo-api` SDK installed
- API key with `data-privacy:write` scope (for deletion requests)
- Understanding of GDPR/CCPA requirements
- Audit logging infrastructure

## Klaviyo Data Privacy API

Klaviyo provides a dedicated **Data Privacy API** for GDPR/CCPA profile deletion. When you delete a profile via this API, Klaviyo performs a full GDPR erasure -- the profile is permanently removed and cannot be recovered.

## Instructions

### Step 1: GDPR Profile Deletion (Right to Erasure)

```typescript
import { ApiKeySession, DataPrivacyApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const dataPrivacyApi = new DataPrivacyApi(session);

/**
 * Request profile deletion via Klaviyo's Data Privacy API.
 * Accepts ONE identifier: email, phone_number, or profile ID.
 * Providing multiple identifiers returns an error.
 *
 * WARNING: This is irreversible. Profile is permanently erased.
 */
async function requestProfileDeletion(identifier: {
  email?: string;
  phoneNumber?: string;
  profileId?: string;
}): Promise<void> {
  // Build the profile identifier (only ONE allowed)
  const profileData: any = { type: 'profile' };

  if (identifier.email) {
    profileData.attributes = { email: identifier.email };
  } else if (identifier.phoneNumber) {
    profileData.attributes = { phone_number: identifier.phoneNumber };
  } else if (identifier.profileId) {
    profileData.id = identifier.profileId;
  } else {
    throw new Error('Must provide exactly one identifier: email, phoneNumber, or profileId');
  }

  await dataPrivacyApi.requestProfileDeletion({
    data: {
      type: 'data-privacy-deletion-job',
      attributes: {
        profile: { data: profileData },
      },
    },
  });

  // Audit log (required for compliance)
  await auditLog({
    action: 'GDPR_DELETION_REQUESTED',
    identifier: identifier.email || identifier.phoneNumber || identifier.profileId!,
    service: 'klaviyo',
    timestamp: new Date().toISOString(),
  });

  console.log(`Deletion requested for ${JSON.stringify(identifier)}`);
}

// Usage
await requestProfileDeletion({ email: 'user-wants-deletion@example.com' });
```

### Step 2: Data Subject Access Request (DSAR)

```typescript
import { ProfilesApi, EventsApi, ListsApi } from 'klaviyo-api';

/**
 * Export all Klaviyo data for a given profile (GDPR Article 15).
 * Returns all profile attributes, event history, and list memberships.
 */
async function exportProfileData(email: string): Promise<{
  profile: any;
  events: any[];
  lists: any[];
}> {
  const profilesApi = new ProfilesApi(session);
  const eventsApi = new EventsApi(session);

  // 1. Get profile
  const profiles = await profilesApi.getProfiles({
    filter: `equals(email,"${email}")`,
  });
  const profile = profiles.body.data[0];
  if (!profile) throw new Error(`No profile found for ${email}`);

  // 2. Get profile's events
  const events = await eventsApi.getEvents({
    filter: `equals(profile_id,"${profile.id}")`,
    sort: '-datetime',
  });

  // 3. Get profile's list memberships
  const profileLists = await profilesApi.getProfileLists({ id: profile.id });

  return {
    profile: {
      id: profile.id,
      ...profile.attributes,
    },
    events: events.body.data.map(e => ({
      metric: e.attributes.metricId,
      datetime: e.attributes.datetime,
      properties: e.attributes.eventProperties,
    })),
    lists: profileLists.body.data.map(l => ({
      id: l.id,
      name: l.attributes.name,
    })),
  };
}
```

### Step 3: PII Detection and Redaction in Logs

```typescript
// src/klaviyo/pii.ts

const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\+?\d{10,15}/g },
  { type: 'api_key', regex: /pk_[a-zA-Z0-9]{20,}/g },
];

export function redactPII(text: string): string {
  let redacted = text;
  for (const pattern of PII_PATTERNS) {
    redacted = redacted.replace(pattern.regex, `[REDACTED:${pattern.type}]`);
  }
  return redacted;
}

export function redactObject(data: Record<string, any>): Record<string, any> {
  const sensitiveFields = ['email', 'phoneNumber', 'phone_number', 'firstName', 'lastName', 'apiKey'];
  const redacted = { ...data };

  for (const field of sensitiveFields) {
    if (redacted[field]) {
      redacted[field] = typeof redacted[field] === 'string'
        ? `${redacted[field].substring(0, 3)}***`
        : '[REDACTED]';
    }
  }

  return redacted;
}

// Usage: safe logging of Klaviyo API responses
console.log('Profile data:', redactObject(profile.attributes));
```

### Step 4: Consent Management

```typescript
/**
 * Record consent and subscribe to marketing.
 * Always include consent timestamp for GDPR compliance.
 */
async function recordConsent(
  email: string,
  channels: { email?: boolean; sms?: boolean },
  listId: string,
  consentSource: string
): Promise<void> {
  const subscriptions: any = {};
  const now = new Date().toISOString();

  if (channels.email) {
    subscriptions.email = {
      marketing: { consent: 'SUBSCRIBED', consentTimestamp: now },
    };
  }
  if (channels.sms) {
    subscriptions.sms = {
      marketing: { consent: 'SUBSCRIBED', consentTimestamp: now },
    };
  }

  await profilesApi.subscribeProfiles({
    data: {
      type: 'profile-subscription-bulk-create-job',
      attributes: {
        profiles: {
          data: [{
            type: 'profile' as any,
            attributes: {
              email,
              subscriptions,
            },
          }],
        },
        historicalImport: false,  // Set true for pre-existing consent
      },
      relationships: {
        list: { data: { type: 'list', id: listId } },
      },
    },
  });

  await auditLog({
    action: 'CONSENT_RECORDED',
    identifier: email,
    channels: Object.keys(channels).filter(c => channels[c as keyof typeof channels]),
    source: consentSource,
    timestamp: now,
  });
}
```

### Step 5: Audit Logging

```typescript
// src/klaviyo/audit.ts

interface AuditEntry {
  action: string;
  identifier: string;
  service: string;
  timestamp: string;
  details?: Record<string, any>;
}

async function auditLog(entry: AuditEntry): Promise<void> {
  // Write to your audit database (must be retained per GDPR)
  await db.auditLog.create({
    data: {
      ...entry,
      retainUntil: new Date(Date.now() + 7 * 365 * 24 * 60 * 60 * 1000), // 7 years
    },
  });

  console.log(`[AUDIT] ${entry.action}: ${entry.identifier} at ${entry.timestamp}`);
}
```

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

## Resources

- [Data Privacy API](https://developers.klaviyo.com/en/reference/data_privacy_api_overview)
- [Request Profile Deletion](https://developers.klaviyo.com/en/reference/request_profile_deletion)
- [Consent Collection Guide](https://developers.klaviyo.com/en/docs/collect_email_and_sms_consent_via_api)
- [GDPR Developer Guide](https://gdpr.eu/developers/)

## Next Steps

For enterprise access control, see `klaviyo-enterprise-rbac`.
