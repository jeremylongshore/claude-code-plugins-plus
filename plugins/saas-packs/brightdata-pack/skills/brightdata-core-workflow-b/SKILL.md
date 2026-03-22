---
name: brightdata-core-workflow-b
description: |
  Execute Bright Data secondary workflow: Core Workflow B.
  Use when implementing secondary use case,
  or complementing primary workflow.
  Trigger with phrases like "brightdata secondary workflow",
  "secondary task with brightdata".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data SERP API & Web Scraper API

## Overview

Collect search engine results and trigger large-scale data collections using Bright Data's SERP API and Web Scraper API. SERP API returns structured JSON from Google, Bing, Yahoo, and other search engines. Web Scraper API triggers asynchronous collections with webhook delivery.

## Prerequisites

- Completed `brightdata-install-auth` setup
- SERP API zone or Web Scraper API dataset configured
- API token from Settings > API tokens

## Instructions

### Step 1: SERP API — Synchronous Google Search

```typescript
// serp-api.ts
import 'dotenv/config';

const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;

async function searchGoogle(query: string, country = 'us') {
  // SERP API uses the proxy protocol with JSON response
  const username = `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}-country-${country}`;

  const response = await fetch(
    `https://www.google.com/search?q=${encodeURIComponent(query)}&brd_json=1`,
    {
      headers: {
        'Proxy-Authorization': `Basic ${Buffer.from(`${username}:${BRIGHTDATA_ZONE_PASSWORD}`).toString('base64')}`,
      },
    }
  );

  const results = await response.json();
  console.log(`Query: "${query}"`);
  console.log(`Results: ${results.organic?.length || 0} organic`);

  for (const r of results.organic?.slice(0, 5) || []) {
    console.log(`  ${r.rank}. ${r.title} — ${r.link}`);
  }
  return results;
}

searchGoogle('bright data web scraping').catch(console.error);
```

### Step 2: SERP API — Structured JSON Response

The SERP API returns structured data when you append `&brd_json=1`:

```typescript
interface SERPResponse {
  organic: Array<{
    rank: number;
    title: string;
    link: string;
    description: string;
    displayed_link: string;
  }>;
  paid?: Array<{ title: string; link: string; description: string }>;
  knowledge_graph?: { title: string; description: string };
  related_searches?: string[];
  total_results?: number;
}
```

### Step 3: Web Scraper API — Async Collection with Webhook

```typescript
// web-scraper-api.ts — trigger large-scale collections
import 'dotenv/config';

const API_TOKEN = process.env.BRIGHTDATA_API_TOKEN!;

async function triggerCollection(
  datasetId: string,
  urls: string[],
  webhookUrl?: string
) {
  const params = new URLSearchParams({
    dataset_id: datasetId,
    format: 'json',
    uncompressed_webhook: 'true',
  });
  if (webhookUrl) params.set('endpoint', webhookUrl);

  const response = await fetch(
    `https://api.brightdata.com/datasets/v3/trigger?${params}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(urls.map(url => ({ url }))),
    }
  );

  const result = await response.json();
  console.log('Collection triggered:', result.snapshot_id);
  return result;
}

// Check collection status
async function getCollectionStatus(snapshotId: string) {
  const response = await fetch(
    `https://api.brightdata.com/datasets/v3/snapshot/${snapshotId}?format=json`,
    { headers: { 'Authorization': `Bearer ${API_TOKEN}` } },
  );

  if (response.status === 200) {
    const data = await response.json();
    console.log('Collection complete:', data.length, 'records');
    return data;
  } else if (response.status === 202) {
    console.log('Collection still running...');
    return null;
  }
}
```

### Step 4: Python SERP API

```python
# serp_api.py
import os, requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.environ['BRIGHTDATA_API_TOKEN']

def search_google(query: str, country: str = 'us'):
    """Trigger a SERP API collection via REST."""
    resp = requests.post(
        'https://api.brightdata.com/datasets/v3/trigger',
        params={'dataset_id': 'gd_lwdb4vjm1ehb499uxs', 'format': 'json'},
        headers={'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json'},
        json=[{'keyword': query, 'country': country, 'engine': 'google'}],
    )
    print(f"Snapshot ID: {resp.json().get('snapshot_id')}")
    return resp.json()
```

## Output

- Structured SERP results in JSON with organic, paid, and knowledge graph data
- Async collection snapshot IDs for large-scale scraping
- Webhook delivery of completed datasets

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API token | Regenerate at Settings > API tokens |
| `400 Bad Request` | Invalid dataset_id | Check dataset ID in control panel |
| `202 Accepted` polling | Collection in progress | Poll every 10s until 200 |
| Rate limited | Too many triggers | Max 20 triggers/min per dataset |

## Resources

- [SERP API Docs](https://docs.brightdata.com/scraping-automation/serp-api/overview)
- [Web Scraper API Trigger](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/trigger-a-collection)
- [SERP API GitHub](https://github.com/luminati-io/serp-api)

## Next Steps

For common errors, see `brightdata-common-errors`.
