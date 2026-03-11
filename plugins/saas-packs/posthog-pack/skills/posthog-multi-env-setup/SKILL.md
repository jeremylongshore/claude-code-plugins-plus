---
name: posthog-multi-env-setup
description: |
  Configure PostHog across development, staging, and production environments.
  Use when setting up multi-environment event capture, managing separate PostHog
  projects per environment, or configuring feature flags and recordings by env.
  Trigger with phrases like "posthog environments", "posthog staging",
  "posthog dev prod", "posthog environment setup", "posthog project per env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Multi-Environment Setup

## Overview
Separate PostHog projects per environment is strongly recommended over using one project with event filtering. Each environment gets its own Project API Key (starts with `phc_`) and Project ID.

## Prerequisites
- PostHog Cloud account or self-hosted instance
- Separate PostHog projects for dev, staging, and production
- Project API keys (`phc_...`) and Project IDs for each environment
- Personal API key for admin operations (optional)

## Environment Strategy

| Environment | PostHog Project | Session Recording | Autocapture | Key Source |
|-------------|----------------|-------------------|-------------|------------|
| Development | `myapp-dev` | Disabled | Enabled | `.env.local` |
| Staging | `myapp-staging` | Disabled | Enabled | CI/CD secrets |
| Production | `myapp-production` | Enabled (sampled) | Enabled | Secret manager |

## Instructions

### Step 1: Create Separate PostHog Projects
```
PostHog Cloud: app.posthog.com > New Project
- "myapp-development" -> copy phc_... API key
- "myapp-staging"     -> copy phc_... API key
- "myapp-production"  -> copy phc_... API key
```

### Step 2: Environment-Specific PostHog Configuration
```typescript
// config/posthog.ts
type Env = "development" | "staging" | "production";

interface PostHogConfig {
  apiKey: string;                   // phc_... project key
  host: string;                     // app.posthog.com or self-hosted URL
  sessionRecording: boolean;
  samplingRate: number;             // 0-1 for session recording
}

const configs: Record<Env, PostHogConfig> = {
  development: {
    apiKey: process.env.NEXT_PUBLIC_POSTHOG_KEY_DEV!,
    host: "https://app.posthog.com",
    sessionRecording: false,         // never record in dev
    samplingRate: 0,
  },
  staging: {
    apiKey: process.env.NEXT_PUBLIC_POSTHOG_KEY_STAGING!,
    host: "https://app.posthog.com",
    sessionRecording: false,         // no recordings in staging
    samplingRate: 0,
  },
  production: {
    apiKey: process.env.NEXT_PUBLIC_POSTHOG_KEY_PROD!,
    host: "https://app.posthog.com",
    sessionRecording: true,
    samplingRate: 0.25,              // record 25% of sessions
  },
};

export function getPostHogConfig(): PostHogConfig {
  const env = (process.env.NODE_ENV || "development") as Env;
  const config = configs[env] || configs.development;
  if (!config.apiKey) {
    console.warn(`PostHog API key not set for ${env} -- analytics disabled`);
  }
  return config;
}
```

### Step 3: Next.js PostHog Provider
```typescript
// app/providers.tsx
"use client";
import posthog from "posthog-js";
import { PostHogProvider } from "posthog-js/react";
import { useEffect } from "react";
import { getPostHogConfig } from "../config/posthog";

export function PHProvider({ children }: { children: React.ReactNode }) {
  const config = getPostHogConfig();

  useEffect(() => {
    if (!config.apiKey) return;

    posthog.init(config.apiKey, {
      api_host: config.host,
      disable_session_recording: !config.sessionRecording,
      session_recording: config.sessionRecording
        ? { sampleRate: config.samplingRate }
        : undefined,
      capture_pageview: false,     // use usePathname in Next.js App Router
      loaded: (ph) => {
        if (process.env.NODE_ENV === "development") {
          ph.debug();
        }
      },
    });
  }, []);

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}
```

### Step 4: Server-Side Node.js Setup
```typescript
// lib/posthog-server.ts
import { PostHog } from "posthog-node";

let _client: PostHog | null = null;

export function getPostHogServer(): PostHog {
  if (_client) return _client;

  const config = getPostHogConfig();
  if (!config.apiKey) return { capture: () => {} } as any; // no-op if unconfigured

  _client = new PostHog(config.apiKey, {
    host: config.host,
    flushAt: 20,
    flushInterval: 10000,  # 10000: 10 seconds in ms
  });

  return _client;
}
```

### Step 5: Environment Variable Setup
```bash
# .env.local
NEXT_PUBLIC_POSTHOG_KEY_DEV=phc_dev_abc123
POSTHOG_PROJECT_ID_DEV=12345  # port 12345 - example/test

# .env.staging
NEXT_PUBLIC_POSTHOG_KEY_STAGING=phc_staging_def456
POSTHOG_PROJECT_ID_STAGING=12346  # 12346 = configured value

# Production (GitHub Actions / cloud secret manager)
# NEXT_PUBLIC_POSTHOG_KEY_PROD=phc_prod_xyz789
# POSTHOG_PROJECT_ID_PROD=12347
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Dev events in prod project | Same API key across envs | Use separate projects per env |
| No events captured | `apiKey` not set in env vars | Check `NEXT_PUBLIC_` prefix for client-side keys |
| Session recordings in staging | `sessionRecording: true` in staging | Set `sessionRecording: false` for non-prod |
| `401` from server-side | Wrong key type | Project key (`phc_...`) is for capture; personal key for admin API |

## Examples

### Verify Environment Routing
```typescript
import { getPostHogConfig } from "./config/posthog";

const cfg = getPostHogConfig();
console.log(`PostHog key: ${cfg.apiKey.slice(0, 10)}...`);
console.log(`Session recording: ${cfg.sessionRecording ? "ON" : "OFF"}`);
```

### Feature Flag Rollout Per Environment
```typescript
// Staging project: 100% rollout for QA
// Production project: 10% initial rollout
const flagValue = await posthogServer.getFeatureFlag("new-checkout", userId);
```

## Resources
- [PostHog Multi-Environment Guide](https://posthog.com/docs/feature-flags/multi-environment-feature-flags)
- [PostHog Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [PostHog Node.js SDK](https://posthog.com/docs/libraries/node)

## Next Steps
For webhook setup, see `posthog-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale