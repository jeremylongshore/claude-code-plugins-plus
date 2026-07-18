# Apify SDK Patterns — Worked Examples

Two end-to-end scenarios that compose the patterns from `SKILL.md` and
[patterns.md](patterns.md) into runnable flows.

## Example A: Call a remote Actor safely from an app

Goal: an external Node service runs the hosted `apify/web-scraper` Actor, reads its
dataset, and never throws on failure. It combines the **typed client singleton**
(Pattern 1) with the **safe result wrapper** (Pattern 8).

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';

let instance: ApifyClient | null = null;

export function getApifyClient(): ApifyClient {
  if (!instance) {
    const token = process.env.APIFY_TOKEN;
    if (!token) throw new Error('APIFY_TOKEN is required');
    instance = new ApifyClient({ token });
  }
  return instance;
}
```

```typescript
// src/scrape.ts
import { getApifyClient } from './apify/client';

type Result<T> = { data: T; error: null } | { data: null; error: Error };

async function safeActorCall<T>(
  actorId: string,
  input: Record<string, unknown>,
): Promise<Result<T[]>> {
  try {
    const client = getApifyClient();
    const run = await client.actor(actorId).call(input, { timeout: 300 });

    if (run.status !== 'SUCCEEDED') {
      return { data: null, error: new Error(`Run ${run.status}: ${run.statusMessage}`) };
    }

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    return { data: items as T[], error: null };
  } catch (err) {
    return { data: null, error: err as Error };
  }
}

const result = await safeActorCall<{ url: string; title: string }>(
  'apify/web-scraper', { startUrls: [{ url: 'https://example.com' }] }
);

if (result.error) {
  console.error('Actor call failed:', result.error.message);
} else {
  console.log(`Got ${result.data.length} items`);
}
```

**Expected outcome:** on success, a count of scraped items; on any failure (non-SUCCEEDED
run status or thrown exception), a single logged error message — no uncaught rejection.

## Example B: A two-tier product scraper Actor

Goal: an Actor that crawls product listing pages, follows links to detail pages, and
pushes structured product records. It combines **crawler selection** (Pattern 2), the
**router** (Pattern 7), and **dataset writes** (Pattern 4).

```typescript
import { Actor } from 'apify';
import { CheerioCrawler, createCheerioRouter } from 'crawlee';

const router = createCheerioRouter();

// Listing pages → enqueue detail links
router.addDefaultHandler(async ({ $, enqueueLinks }) => {
  const detailLinks = $('a.product-link')
    .map((_, el) => $(el).attr('href'))
    .get();

  await enqueueLinks({ urls: detailLinks, label: 'DETAIL' });
});

// Detail pages → extract and store one product
router.addHandler('DETAIL', async ({ request, $ }) => {
  await Actor.pushData({
    url: request.url,
    name: $('h1.product-name').text().trim(),
    price: parseFloat($('.price').text().replace('$', '')),
    description: $('div.description').text().trim(),
  });
});

await Actor.main(async () => {
  const crawler = new CheerioCrawler({ requestHandler: router });
  await crawler.run(['https://example-store.com/products']);
});
```

**Expected outcome:** the default dataset fills with one row per product
(`url`, `name`, `price`, `description`), which you can then download as CSV or JSON via
the `apify-client` dataset calls in [patterns.md](patterns.md).
