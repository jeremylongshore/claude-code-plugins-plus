---
name: klaviyo-migration-deep-dive
description: |
  Execute major Klaviyo migration strategies: from legacy v1/v2 APIs, from competitors,
  or full re-platforming to Klaviyo with the strangler fig pattern.
  Trigger with phrases like "migrate to klaviyo", "klaviyo migration",
  "switch to klaviyo", "klaviyo replatform", "mailchimp to klaviyo",
  "legacy to klaviyo", "v1 to v2 klaviyo".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Migration Deep Dive

## Overview

Comprehensive guide for migrating to Klaviyo from legacy APIs (v1/v2), competing ESPs (Mailchimp, SendGrid, etc.), or re-platforming with the strangler fig pattern. Covers data migration, API mapping, and validation.

## Prerequisites

- Target Klaviyo account configured
- `klaviyo-api` SDK installed
- Source system access for data export
- Feature flag infrastructure (for gradual rollout)

## Migration Types

| Migration | Complexity | Duration | Risk |
|-----------|-----------|----------|------|
| Klaviyo v1/v2 to current API | Low-Medium | 1-2 weeks | Low |
| Mailchimp/SendGrid to Klaviyo | Medium | 2-4 weeks | Medium |
| Custom ESP to Klaviyo | High | 4-8 weeks | High |
| Full re-platform | High | 2-3 months | High |

## Instructions

### Step 1: Legacy v1/v2 to Current API

The most common migration. Klaviyo deprecated v1/v2 endpoints in favor of the JSON:API REST API.

```typescript
// ============================================================
// BEFORE: Legacy v1/v2 endpoints (DEPRECATED, will stop working)
// ============================================================

// v1 Track (event tracking)
// POST https://a.klaviyo.com/api/track
// Body: { token: "PUBLIC_KEY", event: "Placed Order", ... }

// v2 List Subscribe
// POST https://a.klaviyo.com/api/v2/list/LIST_ID/subscribe
// Headers: { api-key: "pk_***" }

// v1 Identify (profile creation)
// POST https://a.klaviyo.com/api/identify
// Body: { token: "PUBLIC_KEY", properties: { $email: "..." } }

// ============================================================
// AFTER: Current REST API (revision 2024-10-15)
// ============================================================

import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ProfileEnum,
  EventEnum,
} from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
const eventsApi = new EventsApi(session);

// v1 Identify → createOrUpdateProfile
await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'user@example.com',     // was $email
      firstName: 'Jane',              // was $first_name
      lastName: 'Doe',                // was $last_name
      phoneNumber: '+15551234567',    // was $phone_number
      properties: {                   // custom properties stay the same
        plan: 'pro',
        signupDate: '2024-01-15',
      },
    },
  },
});

// v1 Track → createEvent
await eventsApi.createEvent({
  data: {
    type: EventEnum.Event,
    attributes: {
      metric: {
        data: { type: 'metric', attributes: { name: 'Placed Order' } },
      },
      profile: {
        data: { type: ProfileEnum.Profile, attributes: { email: 'user@example.com' } },
      },
      properties: {
        orderId: 'ORD-123',
        items: [{ name: 'Widget', price: 29.99 }],
      },
      value: 29.99,
      time: new Date().toISOString(),
      uniqueId: 'ORD-123',
    },
  },
});

// v2 List Subscribe → subscribeProfiles (bulk)
await profilesApi.subscribeProfiles({
  data: {
    type: 'profile-subscription-bulk-create-job',
    attributes: {
      profiles: {
        data: [{
          type: ProfileEnum.Profile,
          attributes: {
            email: 'user@example.com',
            subscriptions: {
              email: { marketing: { consent: 'SUBSCRIBED', consentTimestamp: new Date().toISOString() } },
            },
          },
        }],
      },
    },
    relationships: {
      list: { data: { type: 'list', id: 'LIST_ID' } },
    },
  },
});
```

### Step 2: API Field Mapping (v1/v2 to Current)

| v1/v2 Field | Current API Field | Notes |
|-------------|-------------------|-------|
| `$email` | `email` | No `$` prefix |
| `$first_name` | `firstName` | camelCase |
| `$last_name` | `lastName` | camelCase |
| `$phone_number` | `phoneNumber` | camelCase, E.164 format |
| `$city` | `location.city` | Nested under `location` |
| `$region` | `location.region` | Nested under `location` |
| `$country` | `location.country` | Nested under `location` |
| `$zip` | `location.zip` | Nested under `location` |
| `$title` | `title` | camelCase |
| `$organization` | `organization` | camelCase |
| Custom props | `properties.yourProp` | Same structure |

### Step 3: Competitor Migration (Mailchimp/SendGrid)

```typescript
// Data migration adapter -- transform competitor data to Klaviyo format

interface CompetitorContact {
  email_address: string;
  first_name: string;
  last_name: string;
  phone: string;
  tags: string[];
  status: 'subscribed' | 'unsubscribed' | 'cleaned';
  stats: { avg_open_rate: number; avg_click_rate: number };
}

function transformToKlaviyo(contact: CompetitorContact) {
  return {
    data: {
      type: 'profile' as const,
      attributes: {
        email: contact.email_address,
        firstName: contact.first_name,
        lastName: contact.last_name,
        phoneNumber: contact.phone ? formatE164(contact.phone) : undefined,
        properties: {
          migrationSource: 'mailchimp',
          migratedAt: new Date().toISOString(),
          previousTags: contact.tags,
          historicalOpenRate: contact.stats.avg_open_rate,
          historicalClickRate: contact.stats.avg_click_rate,
        },
      },
    },
  };
}

// Batch import with progress tracking
async function migrateContacts(contacts: CompetitorContact[]): Promise<{
  imported: number;
  skipped: number;
  failed: string[];
}> {
  let imported = 0;
  let skipped = 0;
  const failed: string[] = [];

  for (let i = 0; i < contacts.length; i += 50) {
    const batch = contacts.slice(i, i + 50);

    const results = await Promise.allSettled(
      batch.map(async contact => {
        // Skip unsubscribed/cleaned -- don't import suppressed contacts
        if (contact.status !== 'subscribed') {
          skipped++;
          return;
        }

        const payload = transformToKlaviyo(contact);
        await profilesApi.createOrUpdateProfile(payload);
        imported++;
      })
    );

    results.forEach((r, idx) => {
      if (r.status === 'rejected') {
        failed.push(batch[idx].email_address);
      }
    });

    console.log(`Progress: ${Math.min(i + 50, contacts.length)}/${contacts.length} (${imported} imported, ${skipped} skipped)`);

    // Respect rate limits
    await new Promise(r => setTimeout(r, 1000));
  }

  return { imported, skipped, failed };
}
```

### Step 4: Strangler Fig Pattern (Gradual Migration)

```typescript
// src/email/service-router.ts

interface EmailService {
  sendCampaign(campaign: CampaignData): Promise<void>;
  trackEvent(event: EventData): Promise<void>;
  getProfile(email: string): Promise<ProfileData>;
}

class LegacyEmailService implements EmailService { /* ... */ }
class KlaviyoEmailService implements EmailService { /* ... */ }

/**
 * Route requests between legacy and Klaviyo based on feature flag.
 * Gradually increase Klaviyo percentage from 0% to 100%.
 */
class MigrationRouter implements EmailService {
  constructor(
    private legacy: EmailService,
    private klaviyo: EmailService,
    private getKlaviyoPercentage: () => number  // Feature flag
  ) {}

  private useKlaviyo(): boolean {
    return Math.random() * 100 < this.getKlaviyoPercentage();
  }

  async trackEvent(event: EventData): Promise<void> {
    if (this.useKlaviyo()) {
      // Send to Klaviyo
      await this.klaviyo.trackEvent(event);
    } else {
      // Send to legacy
      await this.legacy.trackEvent(event);
    }

    // During migration: dual-write to both for comparison
    // Remove dual-write after validation
  }

  async sendCampaign(campaign: CampaignData): Promise<void> {
    // Campaigns always go through one system at a time
    if (this.getKlaviyoPercentage() >= 100) {
      return this.klaviyo.sendCampaign(campaign);
    }
    return this.legacy.sendCampaign(campaign);
  }
}
```

### Step 5: Post-Migration Validation

```typescript
async function validateMigration(sampleSize = 100): Promise<{
  passed: boolean;
  checks: Array<{ name: string; passed: boolean; details: string }>;
}> {
  const checks = [];

  // 1. Profile count comparison
  const profiles = await fetchAllPages(cursor => profilesApi.getProfiles({ pageCursor: cursor }));
  checks.push({
    name: 'Profile count',
    passed: profiles.length >= expectedProfileCount * 0.95,
    details: `Found ${profiles.length}, expected ~${expectedProfileCount}`,
  });

  // 2. Sample profile data integrity
  const sample = profiles.slice(0, sampleSize);
  let dataMatchCount = 0;
  for (const profile of sample) {
    const sourceData = await getSourceProfileData(profile.attributes.email);
    if (sourceData && profile.attributes.firstName === sourceData.first_name) {
      dataMatchCount++;
    }
  }
  checks.push({
    name: 'Data integrity',
    passed: dataMatchCount / sampleSize > 0.98,
    details: `${dataMatchCount}/${sampleSize} profiles match source data`,
  });

  // 3. List membership verification
  const lists = await listsApi.getLists();
  checks.push({
    name: 'Lists created',
    passed: lists.body.data.length >= expectedListCount,
    details: `Found ${lists.body.data.length} lists`,
  });

  return {
    passed: checks.every(c => c.passed),
    checks,
  };
}
```

## Migration Checklist

- [ ] Export all contacts from source system
- [ ] Map fields to Klaviyo format (camelCase, E.164 phones)
- [ ] Exclude suppressed/bounced contacts from import
- [ ] Create lists in Klaviyo before import
- [ ] Import profiles in batches (50-100 per batch, with delays)
- [ ] Verify subscription consent timestamps
- [ ] Recreate segments in Klaviyo
- [ ] Migrate email templates
- [ ] Rebuild flows (welcome series, abandoned cart, etc.)
- [ ] Validate data integrity with sample checks
- [ ] Switch DNS/tracking domain to Klaviyo
- [ ] Monitor deliverability for 2 weeks post-migration
- [ ] Decommission legacy system after 30-day validation

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate profiles | Same email imported twice | Use `createOrUpdateProfile` (upsert) |
| Phone format errors | Non-E.164 format | Pre-validate and format as `+{country}{number}` |
| Rate limited during import | Too fast | Reduce batch size, add delays |
| Missing consent timestamps | Historical data | Set `historicalImport: true` flag |
| Template rendering errors | Incompatible template syntax | Convert to Klaviyo Django template syntax |

## Resources

- [v1/v2 Migration Best Practices](https://developers.klaviyo.com/en/v2024-10-15/docs/best_practices_v1v2_migration)
- [Relationship Migration Guide](https://developers.klaviyo.com/en/v2024-10-15/docs/migrate_to_2023_07_15_relationships)
- [Custom Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
