---
name: klaviyo-core-workflow-a
description: |
  Execute Klaviyo primary workflow: profiles, lists, and subscriptions.
  Use when creating/updating profiles, managing lists, subscribing contacts,
  or syncing customer data to Klaviyo for email/SMS marketing.
  Trigger with phrases like "klaviyo profiles", "klaviyo lists",
  "klaviyo subscribe", "add contacts to klaviyo", "klaviyo customer data".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Core Workflow A -- Profiles, Lists & Subscriptions

## Overview

Primary money-path workflow: create/update profiles, manage lists, and subscribe contacts for email and SMS marketing via the `klaviyo-api` SDK.

## Prerequisites

- Completed `klaviyo-install-auth` setup
- API key with scopes: `profiles:read`, `profiles:write`, `lists:read`, `lists:write`

## Instructions

### Step 1: Create or Update a Profile

```typescript
import { ApiKeySession, ProfilesApi, ProfileEnum } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);

// Create a new profile (409 if email already exists)
const newProfile = await profilesApi.createProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'customer@example.com',
      firstName: 'Jane',
      lastName: 'Doe',
      phoneNumber: '+15551234567',
      location: {
        city: 'Atlanta',
        region: 'GA',
        country: 'US',
        zip: '30309',
      },
      properties: {
        plan: 'pro',
        signupSource: 'website',
        lifetime_value: 250.00,
      },
    },
  },
});
console.log('Profile ID:', newProfile.body.data.id);

// Create OR update (upsert) -- preferred for syncing
const upserted = await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'customer@example.com',
      firstName: 'Jane',
      lastName: 'Doe-Smith',  // Updated last name
      properties: {
        plan: 'enterprise',   // Updated plan
        lastLogin: new Date().toISOString(),
      },
    },
  },
});
console.log('Upserted profile:', upserted.body.data.id);
```

### Step 2: Create a List

```typescript
import { ListsApi, ListEnum } from 'klaviyo-api';

const listsApi = new ListsApi(session);

// Create a new list
const list = await listsApi.createList({
  data: {
    type: ListEnum.List,
    attributes: {
      name: 'Newsletter Subscribers',
    },
  },
});
const listId = list.body.data.id;
console.log('List created:', listId);

// Get all lists
const allLists = await listsApi.getLists();
for (const l of allLists.body.data) {
  console.log(`${l.attributes.name} (${l.id})`);
}
```

### Step 3: Add Profiles to a List

```typescript
// Add existing profiles to a list (does NOT change subscription status)
await listsApi.createListRelationships({
  id: listId,
  relationshipType: 'profiles' as any,
  body: {
    data: [
      { type: ProfileEnum.Profile, id: 'PROFILE_ID_1' },
      { type: ProfileEnum.Profile, id: 'PROFILE_ID_2' },
    ],
  },
});
```

### Step 4: Subscribe Profiles (Email + SMS Consent)

```typescript
// Subscribe profiles to a list WITH marketing consent
// This is the correct way to add subscribers (not just list members)
await profilesApi.subscribeProfiles({
  data: {
    type: 'profile-subscription-bulk-create-job',
    attributes: {
      profiles: {
        data: [
          {
            type: ProfileEnum.Profile,
            attributes: {
              email: 'subscriber@example.com',
              phoneNumber: '+15559876543',
              subscriptions: {
                email: {
                  marketing: {
                    consent: 'SUBSCRIBED',
                    consentTimestamp: new Date().toISOString(),
                  },
                },
                sms: {
                  marketing: {
                    consent: 'SUBSCRIBED',
                    consentTimestamp: new Date().toISOString(),
                  },
                },
              },
            },
          },
        ],
      },
    },
    relationships: {
      list: {
        data: {
          type: ListEnum.List,
          id: listId,
        },
      },
    },
  },
});
console.log('Profile subscribed to email + SMS');
```

### Step 5: Query Profiles with Filters

```typescript
// Filter profiles by custom property
const proUsers = await profilesApi.getProfiles({
  filter: 'equals(properties.plan,"pro")',
  sort: '-created',  // Newest first
});

// Filter by date range
const recentProfiles = await profilesApi.getProfiles({
  filter: 'greater-than(created,2024-01-01T00:00:00Z)',
});

// Filter by email domain
const gmailUsers = await profilesApi.getProfiles({
  filter: 'contains(email,"@gmail.com")',
});

// Get profiles for a specific list
const listMembers = await listsApi.getListProfiles({ id: listId });
for (const member of listMembers.body.data) {
  console.log(member.attributes.email);
}
```

### Step 6: Bulk Profile Import

```typescript
// Batch create/update up to 100 profiles at a time
const profiles = customers.map(c => ({
  type: ProfileEnum.Profile as const,
  attributes: {
    email: c.email,
    firstName: c.firstName,
    lastName: c.lastName,
    properties: { source: 'bulk-import', importedAt: new Date().toISOString() },
  },
}));

// Process in batches of 100
for (let i = 0; i < profiles.length; i += 100) {
  const batch = profiles.slice(i, i + 100);
  await Promise.all(
    batch.map(p => profilesApi.createOrUpdateProfile({ data: p }))
  );
  console.log(`Imported ${Math.min(i + 100, profiles.length)}/${profiles.length}`);
}
```

## Output

- Profiles created/updated in Klaviyo
- Lists created and populated
- Subscribers opted in with consent timestamps
- Queryable customer data for segmentation

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| Duplicate profile | 409 | Email exists | Use `createOrUpdateProfile` (upsert) |
| Invalid phone | 400 | Wrong format | Use E.164 format: `+15551234567` |
| List not found | 404 | Wrong list ID | Verify list ID via `getLists()` |
| Missing consent | 400 | No consent timestamp | Always include `consentTimestamp` |
| Rate limited | 429 | >75 req/s burst | See `klaviyo-rate-limits` |

## Resources

- [Profiles API](https://developers.klaviyo.com/en/reference/profiles_api_overview)
- [Lists API](https://developers.klaviyo.com/en/reference/lists_api_overview)
- [Subscribe Profiles](https://developers.klaviyo.com/en/reference/bulk_subscribe_profiles)
- [Consent Collection Guide](https://developers.klaviyo.com/en/docs/collect_email_and_sms_consent_via_api)

## Next Steps

For event tracking and campaign triggers, see `klaviyo-core-workflow-b`.
