---
name: posthog-deploy-integration
description: |
  Deploy PostHog integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying PostHog-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy posthog", "posthog Vercel",
  "posthog production deploy", "posthog Cloud Run", "posthog Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Deploy Integration

## Overview
Deploy PostHog analytics integration to production. Covers client-side snippet deployment, server-side event capture with `posthog-node`, reverse proxy setup to avoid ad blockers, and self-hosted PostHog deployment using Docker.

## Prerequisites
- PostHog project API key (starts with `phc_`)
- PostHog personal API key for server-side operations
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Client-Side Integration
```typescript
// lib/posthog.ts
import posthog from "posthog-js";

export function initPostHog() {
  if (typeof window !== "undefined") {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      capture_pageview: false, // Manual pageview tracking
      loaded: (posthog) => {
        if (process.env.NODE_ENV === "development") posthog.debug();
      },
    });
  }
}
```

### Step 2: Server-Side Event Capture
```typescript
// lib/posthog-server.ts
import { PostHog } from "posthog-node";

const posthog = new PostHog(process.env.POSTHOG_API_KEY!, {
  host: process.env.POSTHOG_HOST || "https://us.i.posthog.com",
});

export async function trackServerEvent(
  distinctId: string,
  event: string,
  properties?: Record<string, any>
) {
  posthog.capture({ distinctId, event, properties });
  await posthog.flush();
}
```

### Step 3: Reverse Proxy (Avoid Ad Blockers)
```typescript
// next.config.js - Proxy PostHog through your domain
module.exports = {
  async rewrites() {
    return [
      {
        source: "/ingest/static/:path*",
        destination: "https://us-assets.i.posthog.com/static/:path*",
      },
      {
        source: "/ingest/:path*",
        destination: "https://us.i.posthog.com/:path*",
      },
    ];
  },
};
```

### Step 4: Self-Hosted Docker Deployment
```bash
set -euo pipefail
# Deploy PostHog self-hosted
git clone https://github.com/PostHog/posthog.git
cd posthog
docker compose -f docker-compose.hobby.yml up -d

# Your PostHog instance at http://localhost:8000
```

### Step 5: Vercel Deployment
```bash
vercel env add NEXT_PUBLIC_POSTHOG_KEY production
vercel env add NEXT_PUBLIC_POSTHOG_HOST production
vercel env add POSTHOG_API_KEY production  # Server-side key
vercel --prod
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Events not appearing | Wrong API key | Verify `phc_` project key |
| Ad blocker blocking | Direct PostHog requests | Set up reverse proxy |
| Self-hosted slow | Under-provisioned | Increase Docker resources |
| Missing server events | Not flushing | Call `posthog.flush()` in serverless |

## Examples


**Basic usage**: Apply posthog deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize posthog deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [PostHog Documentation](https://posthog.com/docs)
- [PostHog Self-Hosting](https://posthog.com/docs/self-host)
- [PostHog Node SDK](https://posthog.com/docs/libraries/node)

## Next Steps
For webhook handling, see `posthog-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale