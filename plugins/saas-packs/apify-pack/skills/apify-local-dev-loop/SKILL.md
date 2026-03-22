---
name: apify-local-dev-loop
description: |
  Set up local Apify Actor development with Apify CLI and Crawlee.
  Use when creating Actors locally, testing with apify run,
  or establishing a fast develop-test-deploy cycle.
  Trigger: "apify dev setup", "apify local development",
  "develop actor locally", "apify run local".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(apify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Local Dev Loop

## Overview

Build and test Apify Actors on your local machine before deploying to the platform. Uses the Apify CLI (`apify run`) which emulates the platform environment locally, creating local storage directories for datasets, key-value stores, and request queues.

## Prerequisites

- `npm install -g apify-cli` (global CLI)
- `apify login` completed with valid token
- Node.js 18+

## Actor Project Structure

```
my-actor/
├── .actor/
│   ├── actor.json          # Actor metadata and config
│   └── INPUT_SCHEMA.json   # Input schema (auto-generates UI on platform)
├── src/
│   └── main.ts             # Entry point
├── storage/                # Created by apify run (git-ignored)
│   ├── datasets/default/
│   ├── key_value_stores/default/
│   └── request_queues/default/
├── package.json
└── tsconfig.json
```

## Instructions

### Step 1: Create a New Actor Project

```bash
# Create from template (interactive)
apify create my-actor

# Or create from specific template
apify create my-actor --template project_cheerio_crawler_ts
# Templates: project_empty, project_cheerio_crawler_ts,
#   project_playwright_crawler_ts, project_puppeteer_crawler_ts
```

### Step 2: Configure .actor/actor.json

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

### Step 3: Define Input Schema

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

### Step 4: Write the Actor

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

### Step 5: Run Locally

```bash
# Run with default input from storage/key_value_stores/default/INPUT.json
apify run

# Run with input from command line
apify run --input='{"startUrls":[{"url":"https://example.com"}],"maxPages":5}'

# View results
cat storage/datasets/default/*.json | jq '.'

# Or list dataset files
ls storage/datasets/default/
```

### Step 6: Provide Local Input

Create `storage/key_value_stores/default/INPUT.json`:

```json
{
  "startUrls": [{ "url": "https://example.com" }],
  "maxPages": 5
}
```

## Local Storage Emulation

`apify run` creates a `storage/` directory that mirrors platform storage:

| Platform Storage | Local Path | Access via SDK |
|-----------------|------------|----------------|
| Default dataset | `storage/datasets/default/` | `Actor.pushData()` |
| Default KV store | `storage/key_value_stores/default/` | `Actor.setValue()` / `Actor.getValue()` |
| Default request queue | `storage/request_queues/default/` | Managed by crawler |

## Hot Reload Development

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

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `apify: command not found` | CLI not installed | `npm i -g apify-cli` |
| `INPUT.json not found` | No input provided | Create `storage/key_value_stores/default/INPUT.json` |
| `Cannot find module 'apify'` | SDK not installed | `npm install apify crawlee` |
| `Dockerfile not found` | Missing actor config | Run `apify create` or create `.actor/actor.json` |

## Resources

- [Local Actor Development](https://docs.apify.com/platform/actors/development/quick-start/locally)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [Actor Templates](https://docs.apify.com/platform/actors/development/quick-start)

## Next Steps

See `apify-sdk-patterns` for production-ready Actor code patterns.
