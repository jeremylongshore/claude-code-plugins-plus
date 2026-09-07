# Klaviyo Migration Patterns

Full before/after code for the three migration classes you will hit when upgrading
the `klaviyo-api` SDK or moving off the legacy v1/v2 HTTP APIs. Apply the pattern
that matches the errors surfaced by `npx tsc --noEmit` in Step 3 of the workflow.

## Legacy v1/v2 to Current API

The legacy `v1`/`v2` HTTP endpoints (`/api/v2/list/.../subscribe`, `/api/track`,
`/api/identify`) are deprecated. Replace direct HTTP calls with the typed SDK
resource classes against the current REST API revision.

```typescript
// BEFORE: Legacy v1/v2 endpoints (DEPRECATED)
// POST https://a.klaviyo.com/api/v2/list/LIST_ID/subscribe
// POST https://a.klaviyo.com/api/track

// AFTER: Current REST API (2024-10-15)
import { ApiKeySession, ProfilesApi, EventsApi, ProfileEnum } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

// v2 Track → Create Event
const eventsApi = new EventsApi(session);
await eventsApi.createEvent({
  data: {
    type: 'event',
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
      profile: { data: { type: 'profile', attributes: { email: 'user@example.com' } } },
      properties: { orderId: '123' },
      time: new Date().toISOString(),
      value: 99.99,
    },
  },
});

// v2 Identify → Create or Update Profile
const profilesApi = new ProfilesApi(session);
await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'user@example.com',
      firstName: 'Jane',
      properties: { plan: 'pro' },
    },
  },
});
```

## SDK Version Upgrade (e.g., v15 to v21)

Older SDK majors initialized a global config via `ConfigWrapper` and exposed flat
resource objects (`Profiles`, `Events`). v21+ uses a per-instance `ApiKeySession`
passed to each `*Api` class, which is safer for multi-tenant and test isolation.

```typescript
// BEFORE (older SDK versions): ConfigWrapper pattern
// import { ConfigWrapper, Profiles } from 'klaviyo-api';
// ConfigWrapper('pk_***');
// const profiles = await Profiles.getProfiles();

// AFTER (v21+): ApiKeySession pattern
import { ApiKeySession, ProfilesApi } from 'klaviyo-api';
const session = new ApiKeySession('pk_***');
const profilesApi = new ProfilesApi(session);
const profiles = await profilesApi.getProfiles();
```

## Property Casing Changes

Older SDK majors accepted `snake_case` attribute keys mirroring the raw JSON:API
payload. v21+ normalizes every attribute to `camelCase` at the SDK boundary and
serializes to the wire format for you.

```typescript
// BEFORE: Some older versions used snake_case
// { first_name: 'Jane', phone_number: '+1555...' }

// AFTER: SDK v21+ uses camelCase everywhere
{ firstName: 'Jane', phoneNumber: '+15551234567' }
```
