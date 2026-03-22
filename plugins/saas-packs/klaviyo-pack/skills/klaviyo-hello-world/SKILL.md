---
name: klaviyo-hello-world
description: |
  Create a minimal working Klaviyo example with real API calls.
  Use when starting a new Klaviyo integration, testing your setup,
  or learning basic profile creation and event tracking patterns.
  Trigger with phrases like "klaviyo hello world", "klaviyo example",
  "klaviyo quick start", "simple klaviyo code", "first klaviyo call".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Hello World

## Overview

Minimal working example: create a profile, track an event, and query the result using the `klaviyo-api` Node.js SDK against `a.klaviyo.com/api/*`.

## Prerequisites

- Completed `klaviyo-install-auth` setup
- `KLAVIYO_PRIVATE_KEY` set in environment
- `klaviyo-api` package installed

## Instructions

### Step 1: Create a Profile

```typescript
// hello-klaviyo.ts
import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ProfileCreateQuery,
  ProfileEnum,
  EventCreateQueryV2,
  EventEnum,
} from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
const eventsApi = new EventsApi(session);

// Create or update a profile
// NOTE: SDK uses camelCase (firstName, not first_name)
const profilePayload: ProfileCreateQuery = {
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'hello@example.com',
      firstName: 'Hello',
      lastName: 'World',
      properties: {
        source: 'hello-world-script',
        signupDate: new Date().toISOString(),
      },
    },
  },
};

const profile = await profilesApi.createProfile(profilePayload);
console.log('Profile created:', profile.body.data.id);
```

### Step 2: Track an Event

```typescript
// Track a custom event tied to the profile
const eventPayload: EventCreateQueryV2 = {
  data: {
    type: EventEnum.Event,
    attributes: {
      // The metric name -- creates the metric if it doesn't exist
      metric: {
        data: {
          type: 'metric',
          attributes: {
            name: 'Hello World Test',
          },
        },
      },
      // Link to the profile by email
      profile: {
        data: {
          type: ProfileEnum.Profile,
          attributes: {
            email: 'hello@example.com',
          },
        },
      },
      properties: {
        message: 'First event from API!',
        timestamp: new Date().toISOString(),
      },
      time: new Date().toISOString(),
      value: 0,
    },
  },
};

await eventsApi.createEvent(eventPayload);
console.log('Event tracked: Hello World Test');
```

### Step 3: Retrieve the Profile

```typescript
// Fetch profiles filtered by email
const profiles = await profilesApi.getProfiles({
  filter: 'equals(email,"hello@example.com")',
});

const p = profiles.body.data[0];
console.log(`Found: ${p.attributes.firstName} ${p.attributes.lastName}`);
console.log(`ID: ${p.id}`);
console.log(`Created: ${p.attributes.created}`);
```

### Step 4: Complete Script

```typescript
// hello-klaviyo.ts -- full runnable script
import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ProfileEnum,
} from 'klaviyo-api';

async function main() {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
  const profilesApi = new ProfilesApi(session);
  const eventsApi = new EventsApi(session);

  // 1. Create profile
  const profile = await profilesApi.createProfile({
    data: {
      type: ProfileEnum.Profile,
      attributes: {
        email: 'hello@example.com',
        firstName: 'Hello',
        lastName: 'World',
      },
    },
  });
  console.log(`Profile created: ${profile.body.data.id}`);

  // 2. Track event
  await eventsApi.createEvent({
    data: {
      type: 'event',
      attributes: {
        metric: { data: { type: 'metric', attributes: { name: 'Hello World Test' } } },
        profile: { data: { type: 'profile', attributes: { email: 'hello@example.com' } } },
        properties: { source: 'hello-world' },
        time: new Date().toISOString(),
      },
    },
  });
  console.log('Event tracked successfully');

  // 3. Query profile back
  const result = await profilesApi.getProfiles({
    filter: 'equals(email,"hello@example.com")',
  });
  console.log(`Verified: ${result.body.data[0]?.attributes.firstName}`);
}

main().catch(console.error);
```

Run it:
```bash
npx tsx hello-klaviyo.ts
```

## Output

```
Profile created: 01JXXXXXXXXXXXXXXXXXXXXXX
Event tracked successfully
Verified: Hello
```

## Error Handling

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `Duplicate profile` | 409 | Email already exists | Use `createOrUpdateProfile` instead |
| `Invalid email format` | 400 | Malformed email | Validate email before sending |
| `Missing metric name` | 400 | Empty metric object | Always include `metric.data.attributes.name` |
| `Unauthorized` | 401 | Bad API key | Check `KLAVIYO_PRIVATE_KEY` env var |

## Key SDK Conventions

- **camelCase properties**: The SDK uses `firstName`, `phoneNumber`, `lastName` (not snake_case)
- **JSON:API format**: All payloads use `{ data: { type, attributes } }` structure
- **Response body**: Access via `response.body.data` (not `response.data`)
- **Profile identifiers**: Use `email`, `phoneNumber`, or `externalId` to identify profiles

## Resources

- [Create Profile API](https://developers.klaviyo.com/en/reference/create_profile)
- [Create Event API](https://developers.klaviyo.com/en/reference/create_event)
- [Get Profiles API](https://developers.klaviyo.com/en/reference/get_profiles)
- [klaviyo-api-node Examples](https://github.com/klaviyo/klaviyo-api-node)

## Next Steps

Proceed to `klaviyo-local-dev-loop` for development workflow setup, or `klaviyo-core-workflow-a` for profile and list management.
