---
name: brightdata-sdk-patterns
description: |
  Apply production-ready Bright Data SDK patterns for TypeScript and Python.
  Use when implementing Bright Data integrations, refactoring SDK usage,
  or establishing team coding standards for Bright Data.
  Trigger with phrases like "brightdata SDK patterns", "brightdata best practices",
  "brightdata code patterns", "idiomatic brightdata".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data SDK Patterns

## Overview

Production-ready patterns for Bright Data proxy integrations. Since Bright Data uses HTTP proxy protocols (not a dedicated SDK), these patterns wrap proxy configuration, retry logic, session management, and response parsing into reusable modules.

## Prerequisites

- Completed `brightdata-install-auth` setup
- Familiarity with async/await and HTTP proxy protocols
- axios or node-fetch installed

## Instructions

### Step 1: Proxy Client Singleton

```typescript
// src/brightdata/client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import https from 'https';
import 'dotenv/config';

let instance: AxiosInstance | null = null;

export function getBrightDataClient(options?: {
  country?: string;
  session?: string;
  zone?: string;
}): AxiosInstance {
  const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;
  const zone = options?.zone || BRIGHTDATA_ZONE!;

  let username = `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${zone}`;
  if (options?.country) username += `-country-${options.country}`;
  if (options?.session) username += `-session-${options.session}`;

  if (!instance || options) {
    instance = axios.create({
      proxy: {
        host: 'brd.superproxy.io',
        port: 33335,
        auth: { username, password: BRIGHTDATA_ZONE_PASSWORD! },
      },
      httpsAgent: new https.Agent({ rejectUnauthorized: false }),
      timeout: 60000,
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; Scraper/1.0)' },
    });
  }
  return instance;
}
```

### Step 2: Retry Wrapper with Proxy Error Handling

```typescript
// src/brightdata/retry.ts
export async function scrapeWithRetry<T>(
  url: string,
  parser: (html: string) => T,
  config = { maxRetries: 3, baseDelayMs: 2000, maxDelayMs: 30000 }
): Promise<T> {
  const client = getBrightDataClient();

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await client.get(url);
      return parser(response.data);
    } catch (error: any) {
      const status = error.response?.status;
      // Bright Data proxy errors that warrant retry
      const retryable = [502, 503, 407, 429].includes(status) || error.code === 'ETIMEDOUT';

      if (attempt === config.maxRetries || !retryable) throw error;

      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        config.maxDelayMs
      );
      console.log(`Attempt ${attempt + 1} failed (${status || error.code}), retrying in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 3: Session Management for Sticky IPs

```typescript
// src/brightdata/sessions.ts — maintain same IP across requests
import { v4 as uuidv4 } from 'uuid';

export class StickySession {
  private sessionId: string;
  private client: AxiosInstance;

  constructor(country?: string) {
    this.sessionId = uuidv4();
    this.client = getBrightDataClient({
      country,
      session: this.sessionId, // Same session = same exit IP
    });
  }

  async get(url: string) {
    return this.client.get(url);
  }

  // Create new session (rotates IP)
  rotate(): void {
    this.sessionId = uuidv4();
    this.client = getBrightDataClient({ session: this.sessionId });
  }
}

// Usage: login flow that needs consistent IP
const session = new StickySession('us');
await session.get('https://example.com/login'); // IP: 1.2.3.4
await session.get('https://example.com/dashboard'); // IP: 1.2.3.4 (same)
session.rotate();
await session.get('https://example.com/other'); // IP: 5.6.7.8 (new)
```

### Step 4: HTML Response Parser with Cheerio

```typescript
// src/brightdata/parser.ts
import * as cheerio from 'cheerio';

export function parseProductPage(html: string) {
  const $ = cheerio.load(html);
  return {
    title: $('h1').first().text().trim(),
    price: $('[data-price], .price').first().text().trim(),
    description: $('meta[name="description"]').attr('content') || '',
    images: $('img[src]').map((_, el) => $(el).attr('src')).get().slice(0, 10),
    inStock: !$('.out-of-stock').length,
  };
}

export function parseSearchResults(html: string) {
  const $ = cheerio.load(html);
  return $('div.g, [data-result]').map((i, el) => ({
    rank: i + 1,
    title: $(el).find('h3').text().trim(),
    link: $(el).find('a').attr('href') || '',
    snippet: $(el).find('.VwiC3b, .st').text().trim(),
  })).get();
}
```

### Step 5: Python Context Manager

```python
# brightdata/client.py
import os, requests
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

@contextmanager
def brightdata_session(country=None, city=None):
    """Context manager for Bright Data proxy sessions."""
    cid = os.environ['BRIGHTDATA_CUSTOMER_ID']
    zone = os.environ['BRIGHTDATA_ZONE']
    pwd = os.environ['BRIGHTDATA_ZONE_PASSWORD']

    username = f'brd-customer-{cid}-zone-{zone}'
    if country: username += f'-country-{country}'
    if city: username += f'-city-{city}'

    proxy_url = f'http://{username}:{pwd}@brd.superproxy.io:33335'
    session = requests.Session()
    session.proxies = {'http': proxy_url, 'https': proxy_url}
    session.verify = './brd-ca.crt'
    session.headers['User-Agent'] = 'Mozilla/5.0'

    try:
        yield session
    finally:
        session.close()

# Usage
with brightdata_session(country='us') as s:
    resp = s.get('https://example.com')
    print(resp.status_code)
```

## Output

- Reusable proxy client singleton with geo-targeting
- Retry wrapper handling 502, 503, 407, 429, and timeouts
- Sticky session management for multi-step scraping flows
- HTML parsing utilities with cheerio
- Python context manager pattern

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton client | All proxy requests | Consistent config, connection reuse |
| Retry wrapper | Transient proxy errors | Auto-recovery from 502/503 |
| Sticky sessions | Login flows, pagination | Same IP across requests |
| Response cache | Development | Avoids burning proxy credits |

## Resources

- [Bright Data Proxy Docs](https://docs.brightdata.com/general/account/proxy-infrastructure)
- [Session Management](https://docs.brightdata.com/general/account/proxy-infrastructure#sessions)
- [Cheerio Documentation](https://cheerio.js.org/)

## Next Steps

Apply patterns in `brightdata-core-workflow-a` for real-world browser scraping.
