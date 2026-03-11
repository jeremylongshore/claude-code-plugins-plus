---
name: posthog-data-handling
description: |
  Implement PostHog PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for PostHog integrations.
  Trigger with phrases like "posthog data", "posthog PII",
  "posthog GDPR", "posthog data retention", "posthog privacy", "posthog CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# PostHog Data Handling

## Overview
Manage analytics data privacy in PostHog. Covers property sanitization before event capture, user opt-out/consent management, data deletion for GDPR compliance, and configuring PostHog's built-in privacy controls.

## Prerequisites
- PostHog project (Cloud or self-hosted)
- `posthog-js` and/or `posthog-node` SDKs
- Understanding of GDPR data subject rights
- Privacy policy covering analytics data

## Instructions

### Step 1: Configure Privacy-Safe Event Capture
```typescript
import posthog from 'posthog-js';

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://us.i.posthog.com',
  autocapture: false,          // Disable to control what's captured
  capture_pageview: true,
  capture_pageleave: true,
  mask_all_text: false,
  mask_all_element_attributes: false,

  // Sanitize properties before sending
  sanitize_properties: (properties, eventName) => {
    // Remove PII from all events
    delete properties['$ip'];
    delete properties['email'];

    // Redact URLs containing tokens
    if (properties['$current_url']) {
      properties['$current_url'] = properties['$current_url']
        .replace(/token=[^&]+/g, 'token=[REDACTED]')
        .replace(/key=[^&]+/g, 'key=[REDACTED]');
    }

    return properties;
  },

  // Respect Do Not Track
  respect_dnt: true,
  opt_out_capturing_by_default: false,
});
```

### Step 2: Consent-Based Tracking
```typescript
// Cookie consent integration
function handleConsentChange(consent: {
  analytics: boolean;
  marketing: boolean;
}) {
  if (consent.analytics) {
    posthog.opt_in_capturing();
  } else {
    posthog.opt_out_capturing();
    posthog.reset(); // Clear local data
  }
}

// Check consent before identifying users
function identifyWithConsent(
  userId: string,
  traits: Record<string, any>,
  hasConsent: boolean
) {
  if (!hasConsent) return;

  // Only send non-PII traits
  const safeTraits: Record<string, any> = {
    plan: traits.plan,
    signup_date: traits.signupDate,
    account_type: traits.accountType,
  };

  // Explicitly exclude PII
  // Do NOT send: email, name, phone, address
  posthog.identify(userId, safeTraits);
}
```

### Step 3: GDPR Data Deletion
```typescript
// Server-side: delete user data for GDPR requests
async function deleteUserData(distinctId: string) {
  const response = await fetch(
    `https://us.i.posthog.com/api/person/${distinctId}/delete/`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        delete_events: true, // Also delete all events from this user
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete user data: ${response.status}`);
  }

  return { deletedUser: distinctId, status: 'completed' };
}

// Find person by property for deletion lookup
async function findPersonByEmail(email: string) {
  const response = await fetch(
    `https://us.i.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/persons/?properties=[{"key":"email","value":"${email}","type":"person"}]`,
    {
      headers: {
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
      },
    }
  );

  const data = await response.json();
  return data.results?.[0]?.distinct_ids?.[0];
}
```

### Step 4: Property Filtering for Exports
```typescript
// Filter sensitive properties from HogQL exports
async function safeExport(query: string) {
  const BLOCKED_PROPERTIES = ['$ip', 'email', 'phone', 'name', 'address'];

  const response = await fetch(
    `https://us.i.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/query/`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: { kind: 'HogQLQuery', query },
      }),
    }
  );

  const data = await response.json();

  // Strip blocked columns from results
  if (data.columns && data.results) {
    const blockedIndexes = data.columns
      .map((col: string, i: number) => BLOCKED_PROPERTIES.some(b => col.includes(b)) ? i : -1)
      .filter((i: number) => i >= 0);

    data.results = data.results.map((row: any[]) =>
      row.filter((_: any, i: number) => !blockedIndexes.includes(i))
    );
    data.columns = data.columns.filter((_: string, i: number) => !blockedIndexes.includes(i));
  }

  return data;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in events | Autocapture sending form data | Disable autocapture, use manual capture |
| Consent not respected | opt_out not called | Check consent state on every page load |
| Deletion failed | Wrong distinct_id | Look up person by email first |
| IP in events | Not stripped | Use `sanitize_properties` to remove `$ip` |

## Examples

### GDPR Subject Access Request
```typescript
async function handleSAR(email: string) {
  const distinctId = await findPersonByEmail(email);
  if (!distinctId) return { found: false };

  // Export their data (filtered)
  const data = await safeExport(
    `SELECT event, timestamp, properties FROM events WHERE distinct_id = '${distinctId}' LIMIT 1000`
  );
  return { found: true, events: data.results.length };
}
```

## Resources
- [PostHog Privacy Controls](https://posthog.com/docs/privacy)
- [PostHog GDPR](https://posthog.com/docs/privacy/gdpr-compliance)
