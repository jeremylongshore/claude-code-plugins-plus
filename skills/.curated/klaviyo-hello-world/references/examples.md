# Klaviyo Hello World — Worked Examples

## Complete runnable script

This is the full end-to-end script combining all three operations from
[implementation.md](implementation.md) into one file you can run directly.

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

Expected console output:

```
Profile created: 01JXXXXXXXXXXXXXXXXXXXXXX
Event tracked successfully
Verified: Hello
```

## Variation: upsert an existing profile

If the email already exists, `createProfile` returns a 409. Switch to
`createOrUpdateProfile` to make the script idempotent — safe to re-run without
duplicate errors:

```typescript
const profile = await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'hello@example.com',
      firstName: 'Hello',
      lastName: 'World',
    },
  },
});
console.log(`Profile upserted: ${profile.body.data.id}`);
```

## Variation: track an event with a monetary value

Set `value` (and optionally `unique_id` for idempotency) when the event
represents revenue, e.g. a "Placed Order" metric:

```typescript
await eventsApi.createEvent({
  data: {
    type: 'event',
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
      profile: { data: { type: 'profile', attributes: { email: 'hello@example.com' } } },
      properties: { orderId: 'ORD-1001', items: 2 },
      value: 49.99,
      time: new Date().toISOString(),
    },
  },
});
```
