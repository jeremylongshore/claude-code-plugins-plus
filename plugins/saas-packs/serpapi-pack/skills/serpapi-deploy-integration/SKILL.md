---
name: serpapi-deploy-integration
description: |
  Deploy SerpApi-powered search features to production platforms.
  Use when deploying search APIs, configuring backend proxies,
  or setting up SerpApi in serverless environments.
  Trigger: "deploy serpapi", "serpapi Vercel", "serpapi production deploy".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Deploy Integration

## Overview

Deploy SerpApi-powered search as a backend API endpoint. Always proxy through your server -- never expose the API key to browsers.

## Instructions

### Vercel Serverless Function

```typescript
// api/search.ts
import { getJson } from 'serpapi';

export default async function handler(req: Request) {
  const url = new URL(req.url);
  const q = url.searchParams.get('q');
  if (!q) return new Response('Missing q parameter', { status: 400 });

  const engine = url.searchParams.get('engine') || 'google';
  const num = parseInt(url.searchParams.get('num') || '5');

  const result = await getJson({
    engine, q, num,
    api_key: process.env.SERPAPI_API_KEY,
  });

  return Response.json({
    results: result.organic_results?.slice(0, num) || [],
    answer_box: result.answer_box || null,
    total_results: result.search_information?.total_results,
  });
}
```

```bash
vercel env add SERPAPI_API_KEY production
vercel --prod
```

### Cloud Run with Python

```python
# main.py
from flask import Flask, request, jsonify
import serpapi, os

app = Flask(__name__)
client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

@app.route("/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Missing q parameter"}), 400

    result = client.search(engine="google", q=q, num=5)
    return jsonify({
        "results": result.get("organic_results", [])[:5],
        "answer_box": result.get("answer_box"),
    })
```

```bash
gcloud run deploy search-api \
  --source . --region us-central1 \
  --set-secrets=SERPAPI_API_KEY=serpapi-key:latest \
  --allow-unauthenticated
```

### Health Check

```typescript
app.get('/health', async (req, res) => {
  const account = await fetch(
    `https://serpapi.com/account.json?api_key=${process.env.SERPAPI_API_KEY}`
  ).then(r => r.json());

  res.json({
    status: account.plan_searches_left > 0 ? 'healthy' : 'credits_exhausted',
    remaining: account.plan_searches_left,
  });
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start slow | First request initializes | Pre-warm with min instances |
| Credits run out | No budget monitoring | Add health check with credit count |
| Key exposed | Frontend calling SerpApi directly | Always proxy through backend |

## Resources

- [Vercel Functions](https://vercel.com/docs/functions)
- [Cloud Run](https://cloud.google.com/run/docs)

## Next Steps

For webhook-like patterns, see `serpapi-webhooks-events`.
