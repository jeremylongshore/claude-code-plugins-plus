---
name: posthog-install-auth
description: |
  Install and configure PostHog SDKs with authentication.
  Use when setting up posthog-js (browser), posthog-node (server),
  or configuring API keys for a new PostHog integration.
  Trigger: "install posthog", "setup posthog", "posthog auth",
  "configure posthog API key", "posthog init".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api, authentication]
---

# PostHog Install & Auth

## Overview

Install PostHog SDKs and configure authentication. PostHog uses two key types: **Project API Key** (`phc_...`) for event capture (public, safe for frontend) and **Personal API Key** (`phx_...`) for private API endpoints (never expose to clients).

## Prerequisites

- Node.js 20+ or Python 3.10+
- PostHog account at [app.posthog.com](https://app.posthog.com)
- Project API key from Project Settings > Project API Key
- Personal API key from Settings > Personal API Keys (for server-side admin)

## Instructions

### Step 1: Install the SDK

```bash
set -euo pipefail
# Browser SDK (posthog-js)
npm install posthog-js

# Node.js server SDK (posthog-node)
npm install posthog-node

# Python SDK
pip install posthog
```

### Step 2: Configure Environment Variables

```bash
# .env (add to .gitignore — never commit)
NEXT_PUBLIC_POSTHOG_KEY=phc_your_project_api_key    # Safe for frontend
POSTHOG_HOST=https://us.i.posthog.com               # US Cloud (or eu.i.posthog.com)
POSTHOG_PERSONAL_API_KEY=phx_your_personal_key      # Server-only, never expose
POSTHOG_PROJECT_ID=12345                             # From project URL
```

### Step 3: Initialize Browser SDK (posthog-js)

```typescript
// lib/posthog.ts
import posthog from 'posthog-js';

export function initPostHog() {
  if (typeof window === 'undefined') return;

  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
    capture_pageview: true,        // Auto-capture $pageview
    capture_pageleave: true,       // Auto-capture $pageleave
    autocapture: true,             // Auto-capture clicks, inputs, form submits
    persistence: 'localStorage+cookie',
    loaded: (ph) => {
      if (process.env.NODE_ENV === 'development') {
        ph.debug();  // Logs all events to console
      }
    },
  });
}
```

### Step 4: Initialize Server SDK (posthog-node)

```typescript
// lib/posthog-server.ts
import { PostHog } from 'posthog-node';

let client: PostHog | null = null;

export function getPostHog(): PostHog {
  if (!client) {
    client = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      host: process.env.POSTHOG_HOST || 'https://us.i.posthog.com',
      flushAt: 20,           // Send batch when 20 events queued
      flushInterval: 10000,  // Or every 10 seconds
      personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY, // Enables local flag eval
    });
  }
  return client;
}

// CRITICAL: Flush before process exits (especially in serverless)
export async function shutdownPostHog() {
  if (client) {
    await client.shutdown();
    client = null;
  }
}
```

### Step 5: Initialize Python SDK

```python
import posthog
import os

posthog.project_api_key = os.getenv('NEXT_PUBLIC_POSTHOG_KEY')
posthog.host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
posthog.personal_api_key = os.getenv('POSTHOG_PERSONAL_API_KEY')
posthog.debug = os.getenv('NODE_ENV') == 'development'

# Capture an event
posthog.capture('user-123', 'my_event', {'property_key': 'value'})
```

### Step 6: Verify Connection

```typescript
import { getPostHog } from './posthog-server';

async function verifyPostHog() {
  const ph = getPostHog();
  ph.capture({
    distinctId: 'test-setup',
    event: 'posthog_setup_verified',
    properties: { source: 'install-auth-skill' },
  });
  await ph.flush();
  console.log('PostHog event sent — check Activity tab in app.posthog.com');
}

verifyPostHog();
```

## API Key Reference

| Key Type | Prefix | Use | Expose to Client? |
|----------|--------|-----|-------------------|
| Project API Key | `phc_` | Capture events, evaluate flags | Yes (public) |
| Personal API Key | `phx_` | Admin API, local flag eval, HogQL queries | Never |

## API Hosts

| Region | Ingest Host | App Host |
|--------|------------|----------|
| US Cloud | `https://us.i.posthog.com` | `https://us.posthog.com` |
| EU Cloud | `https://eu.i.posthog.com` | `https://eu.posthog.com` |
| Self-hosted | Your domain | Your domain |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `posthog.init` ignored | Called server-side | Guard with `typeof window !== 'undefined'` |
| Events not appearing | Wrong API key prefix | Use `phc_` project key for capture |
| `401 Unauthorized` on API | Personal key expired/missing | Generate new key in Settings > Personal API Keys |
| `ECONNREFUSED` | Wrong host URL | Verify US vs EU region in `api_host` |
| Module not found | SDK not installed | Run `npm install posthog-js` or `npm install posthog-node` |

## Output

- Installed PostHog SDK(s) in `node_modules` or `site-packages`
- `.env` file with project and personal API keys
- Initialization code for browser and/or server
- Verified event delivery to PostHog dashboard

## Resources

- [PostHog API Overview](https://posthog.com/docs/api)
- [posthog-js Documentation](https://posthog.com/docs/libraries/js)
- [posthog-node Documentation](https://posthog.com/docs/libraries/node)
- [PostHog Python SDK](https://posthog.com/docs/libraries/python)

## Next Steps

After setup, proceed to `posthog-hello-world` for your first event capture.
