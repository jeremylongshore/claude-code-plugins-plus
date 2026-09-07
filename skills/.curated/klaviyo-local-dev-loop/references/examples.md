# Klaviyo Local Dev Loop — Test Examples

Complete unit and integration test examples for the Klaviyo local dev loop. Pair
these with the file layout and client singleton in
[implementation.md](implementation.md).

## Step 4: Unit Testing with Mocks

The entire `klaviyo-api` module is mocked so unit tests never touch the network.

```typescript
// tests/unit/profiles.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the entire klaviyo-api module
vi.mock('klaviyo-api', () => ({
  ApiKeySession: vi.fn(),
  ProfilesApi: vi.fn().mockImplementation(() => ({
    createProfile: vi.fn().mockResolvedValue({
      body: {
        data: {
          id: '01JMOCKPROFILEID',
          type: 'profile',
          attributes: { email: 'test@example.com', firstName: 'Test' },
        },
      },
    }),
    getProfiles: vi.fn().mockResolvedValue({
      body: {
        data: [{ id: '01JMOCKPROFILEID', attributes: { email: 'test@example.com' } }],
        links: { next: null },
      },
    }),
  })),
  ProfileEnum: { Profile: 'profile' },
}));

import { ProfilesApi, ApiKeySession } from 'klaviyo-api';

describe('Profile operations', () => {
  let profilesApi: ProfilesApi;

  beforeEach(() => {
    const session = new ApiKeySession('pk_test_key');
    profilesApi = new ProfilesApi(session);
  });

  it('creates a profile with email', async () => {
    const result = await profilesApi.createProfile({
      data: {
        type: 'profile' as any,
        attributes: { email: 'test@example.com', firstName: 'Test' },
      },
    });
    expect(result.body.data.id).toBe('01JMOCKPROFILEID');
  });
});
```

## Step 5: Integration Test (runs against live API)

Gated behind `KLAVIYO_TEST=1` so it only runs in CI or when explicitly opted in.

```typescript
// tests/integration/klaviyo.test.ts
import { describe, it, expect } from 'vitest';
import { ApiKeySession, ProfilesApi, AccountsApi } from 'klaviyo-api';

const SKIP = !process.env.KLAVIYO_TEST;

describe.skipIf(SKIP)('Klaviyo Integration', () => {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

  it('connects to Klaviyo account', async () => {
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();
    expect(result.body.data).toHaveLength(1);
    expect(result.body.data[0].id).toBeTruthy();
  });

  it('creates and retrieves a test profile', async () => {
    const profilesApi = new ProfilesApi(session);
    const testEmail = `test-${Date.now()}@example.com`;

    await profilesApi.createProfile({
      data: {
        type: 'profile' as any,
        attributes: { email: testEmail, firstName: 'IntegrationTest' },
      },
    });

    const profiles = await profilesApi.getProfiles({
      filter: `equals(email,"${testEmail}")`,
    });
    expect(profiles.body.data[0].attributes.firstName).toBe('IntegrationTest');
  });
});
```
