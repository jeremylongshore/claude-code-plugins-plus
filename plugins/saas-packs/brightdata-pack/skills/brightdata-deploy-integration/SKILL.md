---
name: brightdata-deploy-integration
description: |
  Deploy Bright Data integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Bright Data-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy brightdata", "brightdata Vercel",
  "brightdata production deploy", "brightdata Cloud Run", "brightdata Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Deploy Integration

## Overview

Deploy Bright Data scraping applications to cloud platforms with proper secrets management. Key consideration: Bright Data proxy connections require outbound TCP to `brd.superproxy.io` on ports 33335 (proxy) and 9222 (Scraping Browser).

## Prerequisites

- Bright Data production zone credentials
- Platform CLI installed (vercel, fly, or gcloud)
- Application tested in staging

## Instructions

### Step 1: Vercel Deployment (Serverless)

```bash
# Add secrets
vercel env add BRIGHTDATA_CUSTOMER_ID production
vercel env add BRIGHTDATA_ZONE production
vercel env add BRIGHTDATA_ZONE_PASSWORD production
vercel env add BRIGHTDATA_API_TOKEN production
```

```json
// vercel.json
{
  "functions": {
    "api/scrape.ts": {
      "maxDuration": 60
    }
  }
}
```

```typescript
// api/scrape.ts — Vercel serverless function
import type { VercelRequest, VercelResponse } from '@vercel/node';
import axios from 'axios';
import https from 'https';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: 'url required' });

  const proxy = {
    host: 'brd.superproxy.io',
    port: 33335,
    auth: {
      username: `brd-customer-${process.env.BRIGHTDATA_CUSTOMER_ID}-zone-${process.env.BRIGHTDATA_ZONE}`,
      password: process.env.BRIGHTDATA_ZONE_PASSWORD!,
    },
  };

  try {
    const response = await axios.get(url, {
      proxy,
      httpsAgent: new https.Agent({ rejectUnauthorized: false }),
      timeout: 55000, // Leave 5s buffer for Vercel's 60s limit
    });
    res.json({ status: response.status, length: response.data.length });
  } catch (error: any) {
    res.status(502).json({ error: error.message });
  }
}
```

### Step 2: Fly.io Deployment (Long-Running)

```toml
# fly.toml — better for Scraping Browser (needs WebSocket)
app = "my-scraper"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
```

```bash
# Set secrets
fly secrets set BRIGHTDATA_CUSTOMER_ID=c_abc123
fly secrets set BRIGHTDATA_ZONE=web_unlocker_prod
fly secrets set BRIGHTDATA_ZONE_PASSWORD=z_prod_pass
fly secrets set BRIGHTDATA_API_TOKEN=prod_token

# Deploy
fly deploy
```

### Step 3: Google Cloud Run

```bash
# Store secrets in Secret Manager
echo -n "c_abc123" | gcloud secrets create brightdata-customer-id --data-file=-
echo -n "web_unlocker_prod" | gcloud secrets create brightdata-zone --data-file=-
echo -n "z_prod_pass" | gcloud secrets create brightdata-zone-password --data-file=-

# Deploy with secret mounts
gcloud run deploy scraper \
  --image gcr.io/$PROJECT_ID/scraper \
  --region us-central1 \
  --set-secrets=BRIGHTDATA_CUSTOMER_ID=brightdata-customer-id:latest \
  --set-secrets=BRIGHTDATA_ZONE=brightdata-zone:latest \
  --set-secrets=BRIGHTDATA_ZONE_PASSWORD=brightdata-zone-password:latest \
  --timeout=120 \
  --memory=512Mi
```

### Step 4: Platform Comparison

| Feature | Vercel | Fly.io | Cloud Run |
|---------|--------|--------|-----------|
| Max timeout | 60s (Pro: 300s) | No limit | 3600s |
| WebSocket (Scraping Browser) | No | Yes | No |
| Outbound TCP | Yes | Yes | Yes |
| Best for | Web Unlocker API | Scraping Browser | Batch scraping |
| Cold start | Fast | Configurable | Medium |

### Step 5: Health Check Endpoint

```typescript
// api/health.ts — works on all platforms
export async function GET() {
  try {
    const proxy = { host: 'brd.superproxy.io', port: 33335, auth: { username: `brd-customer-${process.env.BRIGHTDATA_CUSTOMER_ID}-zone-${process.env.BRIGHTDATA_ZONE}`, password: process.env.BRIGHTDATA_ZONE_PASSWORD! } };
    const start = Date.now();
    const res = await axios.get('https://lumtest.com/myip.json', { proxy, httpsAgent: new (await import('https')).Agent({ rejectUnauthorized: false }), timeout: 15000 });
    return Response.json({ status: 'healthy', proxy_ip: res.data.ip, latency_ms: Date.now() - start });
  } catch {
    return Response.json({ status: 'degraded' }, { status: 503 });
  }
}
```

## Output

- Platform-specific deployment with secrets management
- Health check endpoint verifying proxy connectivity
- Timeout and memory configured for scraping workloads

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Vercel timeout | 60s limit too short | Upgrade to Pro (300s) or use Fly.io |
| WebSocket refused | Platform blocks WS | Use Fly.io for Scraping Browser |
| Cold start timeout | Proxy handshake slow | Configure min instances |
| Secrets not found | Wrong env name | Verify with platform CLI |

## Resources

- [Vercel Serverless Limits](https://vercel.com/docs/functions/runtimes#max-duration)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook handling, see `brightdata-webhooks-events`.
