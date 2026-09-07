# Klaviyo Core Workflow A -- Worked Examples

End-to-end scenarios composed from the documented API calls in
[implementation.md](implementation.md). Each example strings the individual
steps into a complete, runnable flow.

## Example 1: Sync a new signup into a newsletter list with consent

Upsert the customer profile, ensure the newsletter list exists, then subscribe
the profile with email + SMS marketing consent in one pass.

```typescript
import {
  ApiKeySession, ProfilesApi, ProfileEnum, ListsApi, ListEnum,
} from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
const profilesApi = new ProfilesApi(session);
const listsApi = new ListsApi(session);

// 1. Upsert the profile (safe on repeat signups -- no 409)
const upserted = await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'customer@example.com',
      firstName: 'Jane',
      lastName: 'Doe',
      properties: { plan: 'pro', signupSource: 'website' },
    },
  },
});

// 2. Create the destination list (or reuse an existing listId)
const list = await listsApi.createList({
  data: { type: ListEnum.List, attributes: { name: 'Newsletter Subscribers' } },
});
const listId = list.body.data.id;

// 3. Subscribe with consent -- this records the opt-in, not just membership
await profilesApi.subscribeProfiles({
  data: {
    type: 'profile-subscription-bulk-create-job',
    attributes: {
      profiles: {
        data: [{
          type: ProfileEnum.Profile,
          attributes: {
            email: 'customer@example.com',
            subscriptions: {
              email: { marketing: { consent: 'SUBSCRIBED', consentTimestamp: new Date().toISOString() } },
            },
          },
        }],
      },
    },
    relationships: { list: { data: { type: ListEnum.List, id: listId } } },
  },
});
console.log('Signup synced + subscribed');
```

## Example 2: Segment pro-plan customers and export their emails

Query by a custom property, then read the list membership for a targeted
campaign audience.

```typescript
// Newest pro-plan customers first
const proUsers = await profilesApi.getProfiles({
  filter: 'equals(properties.plan,"pro")',
  sort: '-created',
});

for (const p of proUsers.body.data) {
  console.log(p.attributes.email, p.attributes.properties.plan);
}
```

## Example 3: Bulk-import a customer CSV into Klaviyo

Map an in-memory customer array to upsert payloads and process in batches of
100 to stay within API limits.

```typescript
const profiles = customers.map(c => ({
  type: ProfileEnum.Profile as const,
  attributes: {
    email: c.email,
    firstName: c.firstName,
    lastName: c.lastName,
    properties: { source: 'bulk-import', importedAt: new Date().toISOString() },
  },
}));

for (let i = 0; i < profiles.length; i += 100) {
  const batch = profiles.slice(i, i + 100);
  await Promise.all(batch.map(p => profilesApi.createOrUpdateProfile({ data: p })));
  console.log(`Imported ${Math.min(i + 100, profiles.length)}/${profiles.length}`);
}
```
