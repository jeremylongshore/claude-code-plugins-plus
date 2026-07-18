# Klaviyo Test Examples — Full Reference

Complete unit and integration test suites referenced by the CI workflow. Unit tests
mock the `klaviyo-api` SDK and run on every PR; integration tests hit the real API
and are gated behind environment variables so they only run when a test key is present.

## Unit test example (mocked SDK)

```typescript
// tests/unit/klaviyo-events.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiKeySession, EventsApi, ProfileEnum } from 'klaviyo-api';

vi.mock('klaviyo-api', () => ({
  ApiKeySession: vi.fn(),
  EventsApi: vi.fn().mockImplementation(() => ({
    createEvent: vi.fn().mockResolvedValue({ body: { data: { id: 'EVT_MOCK' } } }),
    getEvents: vi.fn().mockResolvedValue({
      body: { data: [], links: { next: null } },
    }),
  })),
  ProfileEnum: { Profile: 'profile' },
  EventEnum: { Event: 'event' },
}));

describe('Event Tracking', () => {
  let eventsApi: EventsApi;

  beforeEach(() => {
    eventsApi = new EventsApi(new ApiKeySession('pk_test'));
  });

  it('tracks a purchase event', async () => {
    const result = await eventsApi.createEvent({
      data: {
        type: 'event' as any,
        attributes: {
          metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
          profile: { data: { type: 'profile', attributes: { email: 'test@example.com' } } },
          properties: { orderId: 'ORD-TEST-001', value: 99.99 },
          time: new Date().toISOString(),
        },
      },
    });
    expect(result.body.data.id).toBe('EVT_MOCK');
  });
});
```

## Integration test example (gated, real API)

```typescript
// tests/integration/klaviyo-live.test.ts
import { describe, it, expect } from 'vitest';
import { ApiKeySession, AccountsApi, ProfilesApi, ProfileEnum } from 'klaviyo-api';

const SKIP = !process.env.KLAVIYO_TEST || !process.env.KLAVIYO_PRIVATE_KEY;

describe.skipIf(SKIP)('Klaviyo Live API', () => {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

  it('authenticates successfully', async () => {
    const accountsApi = new AccountsApi(session);
    const accounts = await accountsApi.getAccounts();
    expect(accounts.body.data).toHaveLength(1);
  });

  it('creates and cleans up a test profile', async () => {
    const profilesApi = new ProfilesApi(session);
    const testEmail = `ci-test-${Date.now()}@example.com`;

    const created = await profilesApi.createProfile({
      data: {
        type: ProfileEnum.Profile,
        attributes: {
          email: testEmail,
          firstName: 'CI',
          lastName: 'Test',
          properties: { source: 'github-actions', timestamp: new Date().toISOString() },
        },
      },
    });

    expect(created.body.data.id).toBeTruthy();
    expect(created.body.data.attributes.email).toBe(testEmail);
  });
});
```

The `SKIP` guard (`describe.skipIf`) is the safety valve: absent `KLAVIYO_TEST` and
`KLAVIYO_PRIVATE_KEY`, the whole live suite is skipped rather than failing — so a
developer running `npm test` locally without a key sees green, and the suite only
exercises the real API inside the gated CI job.
