---
name: klaviyo-hello-world
description: 'Create a minimal working Klaviyo example with real API calls.

  Use when starting a new Klaviyo integration, testing your setup,

  or learning basic profile creation and event tracking patterns.

  Trigger with phrases like "klaviyo hello world", "klaviyo example",

  "klaviyo quick start", "simple klaviyo code", "first klaviyo call".

  '
allowed-tools: Write, Bash(npm:*), Bash(npx:*)
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
# Klaviyo Hello World

## Overview

Minimal working example: create a profile, track an event, and query the result
using the `klaviyo-api` Node.js SDK against `a.klaviyo.com/api/*`. This is the
smoke test that proves your API key, SDK install, and network path all work
end-to-end before you build anything real.

## Prerequisites

- Completed the `klaviyo-install-auth` setup so credentials are in place.
- `KLAVIYO_PRIVATE_KEY` exported in your environment (a private API key with
  Profiles and Events scopes).
- `klaviyo-api` installed in the project (`npm install klaviyo-api`).
- `tsx` available to run the TypeScript file (`npx tsx …`).

## Instructions

Write the code into a single `hello-klaviyo.ts` file, then run it with
`npx tsx hello-klaviyo.ts`. The full script performs four things in order:

1. **Create a profile** — `profilesApi.createProfile(...)` with a JSON:API
   payload. The essential skeleton:

   ```typescript
   import { ApiKeySession, ProfilesApi, ProfileEnum } from 'klaviyo-api';

   const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
   const profilesApi = new ProfilesApi(session);

   const profile = await profilesApi.createProfile({
     data: {
       type: ProfileEnum.Profile,
       attributes: { email: 'hello@example.com', firstName: 'Hello', lastName: 'World' },
     },
   });
   console.log('Profile created:', profile.body.data.id);
   ```

2. **Track an event** — `eventsApi.createEvent(...)` with a `metric` (created on
   first use) linked to the profile by email.
3. **Retrieve the profile** — `profilesApi.getProfiles({ filter: '...' })` to
   confirm the write landed.
4. **Run the combined script** — `npx tsx hello-klaviyo.ts`.

For the complete step-by-step code (all payloads with camelCase and JSON:API
detail), see the [full walkthrough](references/implementation.md). For the
single combined runnable script and variations, see
[worked examples](references/examples.md).

## Output

Running the combined script prints one line per operation. The profile ID is a
26-character ULID; `Verified` echoes the `firstName` read back from the API,
proving the round trip succeeded:

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

## Examples

The canonical example is the single combined script that creates a profile,
tracks an event, and reads the profile back — see the
[worked examples](references/examples.md) for the full file plus two common
variations (idempotent upsert with `createOrUpdateProfile`, and a revenue event
that sets `value`). The core shape of every call is the same JSON:API envelope:

```typescript
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
```

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

Proceed to `klaviyo-local-dev-loop` for development workflow setup, or
`klaviyo-core-workflow-a` for profile and list management.
