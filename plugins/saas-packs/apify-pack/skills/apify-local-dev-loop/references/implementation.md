# Apify Local Dev Loop — Full Implementation

Complete configuration and source for a local Apify Actor project: the
`.actor/actor.json` metadata with a dataset view, the input schema, the Crawlee
Actor entry point, hot-reload wiring, and a unit test. Follow the lean steps in
`SKILL.md`, then drill in here for the exact files.

## Configure `.actor/actor.json`

Actor metadata plus an optional dataset `views` block that renders a table on the
platform:

```json
{
  "actorSpecification": 1,
  "name": "my-actor",
  "title": "My Actor",
  "description": "Scrapes data from example.com",
  "version": "0.1",
  "meta": {
    "templateId": "project_cheerio_crawler_ts"
  },
  "input": "./INPUT_SCHEMA.json",
  "dockerfile": "./Dockerfile",
  "storages": {
    "dataset": {
      "actorSpecification": 1,
      "title": "Scraped items",
      "views": {
        "overview": {
          "title": "Overview",
          "transformation": { "fields": ["url", "title", "text"] },
          "display": {
            "component": "table",
            "properties": {
              "url": { "label": "URL", "format": "link" },
              "title": { "label": "Title" },
              "text": { "label": "Content" }
            }
          }
        }
      }
    }
  }
}
```

## Define the Input Schema

`.actor/INPUT_SCHEMA.json` auto-generates the input UI on the platform and
validates local runs:

```json
{
  "title": "My Actor Input",
  "type": "object",
  "schemaVersion": 1,
  "properties": {
    "startUrls": {
      "title": "Start URLs",
      "type": "array",
      "description": "URLs to crawl",
      "editor": "requestListSources",
      "prefill": [{ "url": "https://example.com" }]
    },
    "maxPages": {
      "title": "Max pages",
      "type": "integer",
      "description": "Maximum number of pages to crawl",
      "default": 10,
      "minimum": 1,
      "maximum": 1000
    }
  },
  "required": ["startUrls"]
}
```

## Write the Actor

`src/main.ts` — reads validated input, crawls with Cheerio, and pushes structured
rows to the default dataset:

```typescript
// src/main.ts
import { Actor } from 'apify';
import { CheerioCrawler } from 'crawlee';

await Actor.init();

const input = await Actor.getInput<{
  startUrls: { url: string }[];
  maxPages?: number;
}>();

if (!input?.startUrls?.length) {
  throw new Error('startUrls is required');
}

const crawler = new CheerioCrawler({
  maxRequestsPerCrawl: input.maxPages ?? 10,
  async requestHandler({ request, $, enqueueLinks }) {
    const title = $('title').text().trim();
    const h1 = $('h1').first().text().trim();

    await Actor.pushData({
      url: request.url,
      title,
      h1,
      timestamp: new Date().toISOString(),
    });

    // Enqueue links on the same domain
    await enqueueLinks({ strategy: 'same-domain' });
  },
});

await crawler.run(input.startUrls.map(s => s.url));
await Actor.exit();
```

## Hot Reload Development

Wire `package.json` scripts for watch-mode iteration:

```json
{
  "scripts": {
    "start": "tsx src/main.ts",
    "dev": "tsx watch src/main.ts",
    "test": "vitest"
  }
}
```

```bash
# Direct tsx execution (faster iteration than apify run)
npx tsx src/main.ts

# With environment variables emulating platform
APIFY_IS_AT_HOME=0 APIFY_LOCAL_STORAGE_DIR=./storage npx tsx src/main.ts
```

## Testing Actors

Mock the SDK boundary (`Actor.getInput` / `Actor.pushData`) with Vitest and assert
on the pushed shape:

```typescript
// tests/main.test.ts
import { describe, it, expect, vi } from 'vitest';
import { Actor } from 'apify';

describe('Actor', () => {
  it('should process input correctly', async () => {
    vi.spyOn(Actor, 'getInput').mockResolvedValue({
      startUrls: [{ url: 'https://example.com' }],
      maxPages: 1,
    });

    const pushSpy = vi.spyOn(Actor, 'pushData').mockResolvedValue(undefined);

    // Run actor logic...
    // Assert pushData was called with expected shape
    expect(pushSpy).toHaveBeenCalledWith(
      expect.objectContaining({ url: 'https://example.com' })
    );
  });
});
```
