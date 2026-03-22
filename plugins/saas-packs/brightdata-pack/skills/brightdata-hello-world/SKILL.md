---
name: brightdata-hello-world
description: |
  Create a minimal working Bright Data example.
  Use when starting a new Bright Data integration, testing your setup,
  or learning basic Bright Data API patterns.
  Trigger with phrases like "brightdata hello world", "brightdata example",
  "brightdata quick start", "simple brightdata code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Hello World

## Overview

Scrape a real webpage through Bright Data's Web Unlocker proxy. Web Unlocker handles CAPTCHAs, fingerprinting, and retries automatically — you send a normal HTTP request through the proxy endpoint at `brd.superproxy.io:33335`.

## Prerequisites

- Completed `brightdata-install-auth` setup
- Web Unlocker zone active in Bright Data control panel
- `brd-ca.crt` SSL certificate downloaded

## Instructions

### Step 1: Scrape via Web Unlocker Proxy (Node.js)

```typescript
// hello-brightdata.ts
import axios from 'axios';
import https from 'https';
import 'dotenv/config';

const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;

const proxy = {
  host: 'brd.superproxy.io',
  port: 33335,
  auth: {
    username: `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}`,
    password: BRIGHTDATA_ZONE_PASSWORD!,
  },
};

async function scrape(url: string) {
  const response = await axios.get(url, {
    proxy,
    httpsAgent: new https.Agent({ rejectUnauthorized: false }),
    timeout: 60000,
  });
  console.log(`Status: ${response.status}`);
  console.log(`Content length: ${response.data.length} chars`);
  console.log(response.data.substring(0, 500));
  return response.data;
}

scrape('https://example.com').catch(console.error);
```

### Step 2: Scrape via REST API

```typescript
// hello-brightdata-api.ts
import 'dotenv/config';

async function scrapeViaAPI(url: string) {
  const response = await fetch('https://api.brightdata.com/request', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.BRIGHTDATA_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      zone: process.env.BRIGHTDATA_ZONE,
      url,
      format: 'raw',
    }),
  });
  const html = await response.text();
  console.log(`Status: ${response.status}, Length: ${html.length}`);
  return html;
}

scrapeViaAPI('https://example.com').catch(console.error);
```

### Step 3: Python Version

```python
# hello_brightdata.py
import os, requests
from dotenv import load_dotenv

load_dotenv()
proxy_url = (
    f"http://brd-customer-{os.environ['BRIGHTDATA_CUSTOMER_ID']}"
    f"-zone-{os.environ['BRIGHTDATA_ZONE']}"
    f":{os.environ['BRIGHTDATA_ZONE_PASSWORD']}"
    f"@brd.superproxy.io:33335"
)
response = requests.get(
    'https://example.com',
    proxies={'http': proxy_url, 'https': proxy_url},
    verify='./brd-ca.crt',
    timeout=60,
)
print(f"Status: {response.status_code}, Length: {len(response.text)}")
```

## Geo-Targeting

Add country or city targeting to the proxy username:

```typescript
// Country-level
const username = `brd-customer-${ID}-zone-${ZONE}-country-us`;
// City-level
const username2 = `brd-customer-${ID}-zone-${ZONE}-country-us-city-newyork`;
```

## Output

- Successful HTTP response through Bright Data proxy
- HTML content of the target page
- Rotated IP address per request

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `407 Proxy Auth Required` | Bad credentials | Check `brd-customer-{ID}-zone-{ZONE}` format |
| `502 Bad Gateway` | Target site blocked | Web Unlocker retries; increase timeout |
| `ETIMEDOUT` | CAPTCHA solving delay | Set timeout to 60-120s |
| Empty response | Zone inactive | Verify zone in control panel |

## Resources

- [Web Unlocker Docs](https://docs.brightdata.com/scraping-automation/web-unlocker/send-your-first-request)
- [Web Unlocker API](https://docs.brightdata.com/scraping-automation/web-unlocker/web-unlocker-api)
- [Geo-Targeting](https://docs.brightdata.com/general/account/proxy-infrastructure)

## Next Steps

Proceed to `brightdata-local-dev-loop` for development workflow setup.
