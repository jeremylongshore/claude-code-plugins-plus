# Apify Integration Tests — Full Reference

The complete integration-test suite referenced from `SKILL.md` Step 4. These
tests exercise a live Apify API and are gated on the `APIFY_TOKEN` secret so
they skip automatically in unit-only runs (e.g. fork PRs without secrets).

```typescript
// tests/integration/apify.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { ApifyClient } from 'apify-client';

const SKIP_INTEGRATION = !process.env.APIFY_TOKEN;

describe.skipIf(SKIP_INTEGRATION)('Apify Integration', () => {
  let client: ApifyClient;

  beforeAll(() => {
    client = new ApifyClient({ token: process.env.APIFY_TOKEN });
  });

  it('should authenticate successfully', async () => {
    const user = await client.user().get();
    expect(user.username).toBeTruthy();
  });

  it('should run a test Actor', async () => {
    const run = await client.actor('apify/website-content-crawler').call(
      {
        startUrls: [{ url: 'https://example.com' }],
        maxCrawlPages: 1,
      },
      { timeout: 120, memory: 256 },
    );

    expect(run.status).toBe('SUCCEEDED');
    expect(run.defaultDatasetId).toBeTruthy();

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    expect(items.length).toBeGreaterThan(0);
  }, 180_000); // 3 minute timeout for this test

  it('should create and delete a named dataset', async () => {
    const name = `ci-test-${Date.now()}`;
    const dataset = await client.datasets().getOrCreate(name);
    expect(dataset.id).toBeTruthy();

    await client.dataset(dataset.id).pushItems([
      { test: true, timestamp: new Date().toISOString() },
    ]);

    const { items } = await client.dataset(dataset.id).listItems();
    expect(items).toHaveLength(1);

    // Cleanup
    await client.dataset(dataset.id).delete();
  });
});
```

## Notes

- **Skip gate.** `describe.skipIf(SKIP_INTEGRATION)` keeps CI green when no token
  is present. Wire the token only into the integration job, never the unit job.
- **Cleanup.** The named-dataset test deletes what it creates so repeated CI runs
  do not accumulate orphan datasets on the account.
- **Timeouts.** Live Actor runs are slow — give the "run a test Actor" case a
  generous per-test timeout (3 minutes here) so a cold Actor start does not flake.
