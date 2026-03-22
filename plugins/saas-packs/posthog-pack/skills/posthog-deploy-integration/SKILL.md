---
name: posthog-deploy-integration
description: |
  Deploy PostHog to Vercel, Docker (self-hosted), and Cloud Run.
  Covers Next.js reverse proxy, server-side capture in edge functions,
  self-hosted PostHog setup, and platform-specific environment configuration.
  Trigger: "deploy posthog", "posthog Vercel", "posthog production deploy",
  "posthog Cloud Run", "posthog self-hosted", "posthog Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, deployment]
---

# PostHog Deploy Integration

## Overview

Deploy PostHog analytics to production platforms. Covers Next.js with Vercel (reverse proxy, server-side capture, edge functions), self-hosted PostHog with Docker, and Google Cloud Run deployment patterns.

## Prerequisites

- PostHog project API key (`phc_...`)
- PostHog personal API key (`phx_...`) for server features
- Platform CLI installed (`vercel`, `docker`, or `gcloud`)

## Instructions

### Step 1: Next.js + Vercel Deployment

```bash
set -euo pipefail
# Set environment variables in Vercel
vercel env add NEXT_PUBLIC_POSTHOG_KEY production     # phc_... (public)
vercel env add NEXT_PUBLIC_POSTHOG_HOST production    # /ingest (if using proxy)
vercel env add POSTHOG_PERSONAL_API_KEY production    # phx_... (server-only)
vercel env add POSTHOG_PROJECT_ID production          # Project ID number
```

```typescript
// next.config.js — Reverse proxy to bypass ad blockers
module.exports = {
  async rewrites() {
    return [
      {
        source: '/ingest/static/:path*',
        destination: 'https://us-assets.i.posthog.com/static/:path*',
      },
      {
        source: '/ingest/:path*',
        destination: 'https://us.i.posthog.com/:path*',
      },
    ];
  },
};
```

```typescript
// app/providers.tsx — Client-side PostHog with proxy
'use client';
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';
import { useEffect } from 'react';

export function PHProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: '/ingest', // Routes through your domain's reverse proxy
      capture_pageview: false, // Handle manually in App Router
      capture_pageleave: true,
    });
  }, []);

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}
```

### Step 2: Server-Side Capture in Vercel Edge Functions

```typescript
// app/api/track/route.ts — Server-side event capture
import { PostHog } from 'posthog-node';
import { NextResponse } from 'next/server';

export const runtime = 'edge';

export async function POST(request: Request) {
  const body = await request.json();
  const { userId, event, properties } = body;

  const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    host: 'https://us.i.posthog.com',
    flushAt: 1,       // Immediate flush in serverless
    flushInterval: 0,
  });

  try {
    posthog.capture({ distinctId: userId, event, properties });
    await posthog.shutdown(); // CRITICAL: flush before function exits
    return NextResponse.json({ status: 'ok' });
  } catch (error) {
    return NextResponse.json({ error: 'capture failed' }, { status: 500 });
  }
}
```

### Step 3: Self-Hosted PostHog (Docker)

```bash
set -euo pipefail
# Deploy PostHog self-hosted (hobby tier)
git clone https://github.com/PostHog/posthog.git
cd posthog

# Configure environment
cat > .env <<'EOF'
SECRET_KEY=your-random-secret-key-here
SITE_URL=https://posthog.yourcompany.com
IS_BEHIND_PROXY=true
EOF

# Start PostHog
docker compose -f docker-compose.hobby.yml up -d

# PostHog runs at http://localhost:8000
# Complete setup wizard in browser

# Health check
curl -s http://localhost:8000/_health | jq .
```

```typescript
// Point SDKs to your self-hosted instance
posthog.init('phc_your_key', {
  api_host: 'https://posthog.yourcompany.com', // Your self-hosted URL
});
```

### Step 4: Google Cloud Run Deployment

```bash
set -euo pipefail
# Set secrets in GCP Secret Manager
echo -n "phc_your_key" | gcloud secrets create posthog-project-key --data-file=-
echo -n "phx_your_key" | gcloud secrets create posthog-personal-key --data-file=-

# Deploy with PostHog secrets
gcloud run deploy my-app \
  --image gcr.io/my-project/my-app:latest \
  --set-secrets "NEXT_PUBLIC_POSTHOG_KEY=posthog-project-key:latest" \
  --set-secrets "POSTHOG_PERSONAL_API_KEY=posthog-personal-key:latest" \
  --set-env-vars "POSTHOG_HOST=https://us.i.posthog.com" \
  --region us-central1 \
  --allow-unauthenticated
```

### Step 5: Deploy Annotation (Mark Deployments in PostHog)

```bash
set -euo pipefail
# Create annotation on each deploy so you can correlate metric changes with releases
curl -X POST "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/annotations/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"Deploy: $(git rev-parse --short HEAD) — $(git log -1 --pretty=%s)\",
    \"date_marker\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"scope\": \"project\"
  }"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Events not appearing | Wrong `api_host` | Use `us.i.posthog.com` (not `app.posthog.com`) |
| Ad blocker blocks events | Direct PostHog requests | Set up reverse proxy via Next.js rewrites |
| Edge function events lost | No `shutdown()` call | Always `await posthog.shutdown()` in serverless |
| Self-hosted 502 | Under-provisioned | Increase Docker memory (min 4GB RAM) |
| Cloud Run cold start lag | PostHog init in handler | Move init to module scope, only shutdown in handler |

## Output

- PostHog deployed to chosen platform with secrets configured
- Reverse proxy enabled for ad blocker bypass (Vercel/Next.js)
- Server-side event capture with proper shutdown hooks
- Deployment annotations marking releases in PostHog timeline

## Resources

- [PostHog Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [PostHog Self-Hosting](https://posthog.com/docs/self-host)
- [PostHog Vercel Integration](https://posthog.com/docs/libraries/vercel)
- [PostHog Annotations API](https://posthog.com/docs/api/annotations)

## Next Steps

For webhook handling, see `posthog-webhooks-events`.
