---
name: vercel-hello-world
description: |
  Create a minimal working Vercel deployment with a serverless API route.
  Use when starting a new Vercel project, testing your setup,
  or learning basic Vercel deployment and API route patterns.
  Trigger with phrases like "vercel hello world", "vercel example",
  "vercel quick start", "simple vercel project", "first vercel deploy".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(npm:*), Bash(npx:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, api, quickstart, deployment]

---
# Vercel Hello World

## Overview
Deploy a minimal project to Vercel with a static page and a serverless API route. Confirms your CLI auth, project structure, and deployment pipeline work end to end.

## Prerequisites
- Completed `vercel-install-auth` setup
- Vercel CLI installed and authenticated
- Node.js 18+

## Instructions

### Step 1: Create Project Structure
```bash
mkdir my-vercel-app && cd my-vercel-app
npm init -y
```

Create the static landing page:

```html
<!-- public/index.html -->
<!DOCTYPE html>
<html>
<head><title>Hello Vercel</title></head>
<body>
  <h1>Hello from Vercel</h1>
  <p id="result">Loading...</p>
  <script>
    fetch('/api/hello')
      .then(r => r.json())
      .then(d => document.getElementById('result').textContent = d.message);
  </script>
</body>
</html>
```

### Step 2: Create Serverless API Route
```typescript
// api/hello.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  res.status(200).json({
    message: 'Hello from Vercel Serverless Function!',
    timestamp: new Date().toISOString(),
    region: process.env.VERCEL_REGION || 'local',
  });
}
```

Install the types:
```bash
npm install --save-dev @vercel/node typescript
```

### Step 3: Add vercel.json Configuration
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "s-maxage=0, stale-while-revalidate" }
      ]
    }
  ]
}
```

### Step 4: Deploy Preview
```bash
# Deploy to a preview URL (not production)
vercel

# Output:
# Vercel CLI 39.x.x
# 🔗 Linked to your-team/my-vercel-app
# 🔍 Inspect: https://vercel.com/your-team/my-vercel-app/xxx
# ✅ Preview: https://my-vercel-app-xxx.vercel.app
```

### Step 5: Test the Deployment
```bash
# Test static page
curl -s https://my-vercel-app-xxx.vercel.app/ | head -5

# Test API route
curl -s https://my-vercel-app-xxx.vercel.app/api/hello | jq .
# {
#   "message": "Hello from Vercel Serverless Function!",
#   "timestamp": "2026-03-22T12:00:00.000Z",
#   "region": "iad1"
# }
```

### Step 6: Promote to Production
```bash
# Deploy directly to production
vercel --prod

# Or promote the preview deployment
vercel promote https://my-vercel-app-xxx.vercel.app
```

## Vercel System Environment Variables

These are available in every function at runtime:

| Variable | Value |
|----------|-------|
| `VERCEL` | `"1"` — always set on Vercel |
| `VERCEL_ENV` | `"production"`, `"preview"`, or `"development"` |
| `VERCEL_URL` | Deployment URL (no protocol) |
| `VERCEL_REGION` | Function region (e.g., `iad1`) |
| `VERCEL_GIT_COMMIT_SHA` | Git commit hash |
| `VERCEL_GIT_COMMIT_MESSAGE` | Git commit message |

## Output
- Static page served from Vercel CDN
- Serverless API route returning JSON at `/api/hello`
- Preview URL for testing before production
- Production deployment live on your domain

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `404 NOT_FOUND` on `/api/hello` | File not in `api/` directory | Move file to project root `api/` folder |
| `FUNCTION_INVOCATION_FAILED` | Runtime error in handler | Check function logs: `vercel logs <url>` |
| `BUILD_FAILED` | TypeScript compilation error | Run `npx tsc --noEmit` locally first |
| `NO_RESPONSE_FROM_FUNCTION` | Handler didn't call `res.send/json` | Ensure all code paths return a response |
| `FUNCTION_PAYLOAD_TOO_LARGE` | Response body > 4.5 MB | Paginate or stream the response |

## Resources
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
- [Vercel CLI Deploy](https://vercel.com/docs/cli/deploy)
- [@vercel/node Runtime](https://vercel.com/docs/functions/runtimes/node-js)

## Next Steps
Proceed to `vercel-local-dev-loop` for development workflow setup.
