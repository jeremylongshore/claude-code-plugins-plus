# Klaviyo Hello World — Full Implementation

Step-by-step code for the three core operations: create a profile, track an
event tied to that profile, and query the profile back. Each block is a
self-contained addition to a single `hello-klaviyo.ts` file. For the combined
runnable script, see [examples.md](examples.md).

## Step 1: Create a Profile

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

## Step 2: Track an Event

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

## Step 3: Retrieve the Profile

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
