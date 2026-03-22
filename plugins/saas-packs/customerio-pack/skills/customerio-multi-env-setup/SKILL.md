---
name: customerio-multi-env-setup
description: |
  Configure Customer.io multi-environment setup with workspace isolation.
  Use when setting up dev/staging/prod workspaces, environment-aware
  clients, or Kubernetes config overlays.
  Trigger: "customer.io environments", "customer.io staging",
  "customer.io dev prod", "customer.io workspace isolation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(kubectl:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, multi-environment, kubernetes]

---
# Customer.io Multi-Environment Setup

## Overview

Configure isolated Customer.io environments for dev, staging, and production: separate workspaces per environment, typed configuration with validation, environment-aware client wrappers, Kubernetes ConfigMap overlays, and data isolation verification.

## Prerequisites

- Customer.io account with multiple workspaces (create at fly.customer.io)
- Environment variable management (dotenv, secrets manager)
- CI/CD pipeline for per-environment deployment

## Workspace Strategy

| Environment | Workspace Name | Purpose | Dry Run | Data |
|-------------|---------------|---------|---------|------|
| Local dev | `myapp-dev` | Individual developer testing | Optional | Fake/test data |
| CI | `myapp-ci` | Automated test runs | No | Auto-cleaned test data |
| Staging | `myapp-staging` | Pre-production validation | No | Subset of real data |
| Production | `myapp-prod` | Live users | No | Real user data |

Each workspace has its own Site ID, Track API Key, and App API Key. Create workspaces at Settings > Workspace Settings.

## Instructions

### Step 1: Typed Environment Configuration

```typescript
// config/customerio.ts
import { RegionUS, RegionEU } from "customerio-node";

type CioEnvironment = "development" | "ci" | "staging" | "production";

interface CioEnvConfig {
  siteId: string;
  trackApiKey: string;
  appApiKey: string;
  region: typeof RegionUS | typeof RegionEU;
  dryRun: boolean;
  logLevel: "debug" | "info" | "warn" | "error";
  eventPrefix: string;     // Prefix events in non-prod to prevent confusion
}

function validateConfig(config: CioEnvConfig, env: CioEnvironment): void {
  if (!config.siteId) throw new Error(`Missing CUSTOMERIO_SITE_ID for ${env}`);
  if (!config.trackApiKey) throw new Error(`Missing CUSTOMERIO_TRACK_API_KEY for ${env}`);
  if (env === "production" && config.dryRun) {
    throw new Error("Production cannot be in dry-run mode");
  }
  if (env === "production" && config.eventPrefix) {
    throw new Error("Production must not use event prefix");
  }
}

export function loadCioConfig(): CioEnvConfig {
  const env = (process.env.NODE_ENV ?? "development") as CioEnvironment;
  const region = process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS;

  const config: CioEnvConfig = {
    siteId: process.env.CUSTOMERIO_SITE_ID ?? "",
    trackApiKey: process.env.CUSTOMERIO_TRACK_API_KEY ?? "",
    appApiKey: process.env.CUSTOMERIO_APP_API_KEY ?? "",
    region,
    dryRun: process.env.CUSTOMERIO_DRY_RUN === "true",
    logLevel: (process.env.CUSTOMERIO_LOG_LEVEL as any) ?? (env === "production" ? "warn" : "debug"),
    eventPrefix: process.env.CUSTOMERIO_EVENT_PREFIX ?? (env === "production" ? "" : `${env}_`),
  };

  validateConfig(config, env);
  return config;
}
```

### Step 2: Environment-Aware Client

```typescript
// lib/customerio-env.ts
import { TrackClient, APIClient } from "customerio-node";
import { loadCioConfig } from "../config/customerio";

const config = loadCioConfig();

export class EnvAwareCioClient {
  private track: TrackClient | null;
  private app: APIClient | null;

  constructor() {
    if (config.dryRun) {
      this.track = null;
      this.app = null;
    } else {
      this.track = new TrackClient(config.siteId, config.trackApiKey, {
        region: config.region,
      });
      this.app = config.appApiKey
        ? new APIClient(config.appApiKey, { region: config.region })
        : null;
    }
  }

  async identify(userId: string, attrs: Record<string, any>): Promise<void> {
    const prefixedId = config.eventPrefix
      ? `${config.eventPrefix}${userId}`
      : userId;

    // Tag with environment for debugging
    const envAttrs = {
      ...attrs,
      _cio_env: process.env.NODE_ENV,
    };

    if (config.dryRun) {
      if (config.logLevel === "debug") {
        console.log(`[CIO DRY RUN] identify: ${prefixedId}`, envAttrs);
      }
      return;
    }

    await this.track!.identify(prefixedId, envAttrs);
  }

  async track(userId: string, name: string, data?: Record<string, any>): Promise<void> {
    const prefixedId = config.eventPrefix
      ? `${config.eventPrefix}${userId}`
      : userId;
    const prefixedName = config.eventPrefix
      ? `${config.eventPrefix}${name}`
      : name;

    if (config.dryRun) {
      if (config.logLevel === "debug") {
        console.log(`[CIO DRY RUN] track: ${prefixedId} ${prefixedName}`, data);
      }
      return;
    }

    await this.track!.track(prefixedId, { name: prefixedName, data });
  }

  getAppClient(): APIClient {
    if (!this.app) {
      throw new Error("App API not available (dry-run or missing key)");
    }
    return this.app;
  }
}
```

### Step 3: Environment Files

```bash
# .env.development
NODE_ENV=development
CUSTOMERIO_SITE_ID=dev-workspace-site-id
CUSTOMERIO_TRACK_API_KEY=dev-track-key
CUSTOMERIO_APP_API_KEY=dev-app-key
CUSTOMERIO_REGION=us
CUSTOMERIO_DRY_RUN=false
CUSTOMERIO_EVENT_PREFIX=dev_
CUSTOMERIO_LOG_LEVEL=debug

# .env.staging
NODE_ENV=staging
CUSTOMERIO_SITE_ID=staging-workspace-site-id
CUSTOMERIO_TRACK_API_KEY=staging-track-key
CUSTOMERIO_APP_API_KEY=staging-app-key
CUSTOMERIO_REGION=us
CUSTOMERIO_DRY_RUN=false
CUSTOMERIO_EVENT_PREFIX=staging_
CUSTOMERIO_LOG_LEVEL=info

# .env.production (or use secrets manager)
NODE_ENV=production
CUSTOMERIO_SITE_ID=prod-workspace-site-id
CUSTOMERIO_TRACK_API_KEY=prod-track-key
CUSTOMERIO_APP_API_KEY=prod-app-key
CUSTOMERIO_REGION=us
CUSTOMERIO_DRY_RUN=false
CUSTOMERIO_EVENT_PREFIX=
CUSTOMERIO_LOG_LEVEL=warn
```

### Step 4: Kubernetes ConfigMap Overlays

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: customerio-config
data:
  CUSTOMERIO_REGION: "us"
  CUSTOMERIO_LOG_LEVEL: "info"

---
# k8s/overlays/development/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: customerio-config
data:
  CUSTOMERIO_DRY_RUN: "true"
  CUSTOMERIO_EVENT_PREFIX: "dev_"
  CUSTOMERIO_LOG_LEVEL: "debug"

---
# k8s/overlays/staging/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: customerio-config
data:
  CUSTOMERIO_DRY_RUN: "false"
  CUSTOMERIO_EVENT_PREFIX: "staging_"
  CUSTOMERIO_LOG_LEVEL: "info"

---
# k8s/overlays/production/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: customerio-config
data:
  CUSTOMERIO_DRY_RUN: "false"
  CUSTOMERIO_EVENT_PREFIX: ""
  CUSTOMERIO_LOG_LEVEL: "warn"
```

### Step 5: Data Isolation Verification

```typescript
// scripts/verify-isolation.ts
import { TrackClient, RegionUS } from "customerio-node";

async function verifyIsolation() {
  const envs = ["development", "staging", "production"];
  const testId = `isolation-test-${Date.now()}`;

  for (const env of envs) {
    const siteId = process.env[`CIO_${env.toUpperCase()}_SITE_ID`];
    const apiKey = process.env[`CIO_${env.toUpperCase()}_TRACK_KEY`];
    if (!siteId || !apiKey) {
      console.log(`[SKIP] ${env}: credentials not configured`);
      continue;
    }

    const client = new TrackClient(siteId, apiKey, { region: RegionUS });
    try {
      await client.identify(testId, {
        email: `${testId}@isolation-test.example.com`,
        _test_env: env,
      });
      console.log(`[OK] ${env}: identify succeeded (separate workspace)`);

      // Clean up
      await client.suppress(testId);
      await client.destroy(testId);
    } catch (err: any) {
      console.log(`[FAIL] ${env}: ${err.statusCode} ${err.message}`);
    }
  }
}

verifyIsolation();
```

### Step 6: CI/CD Environment Promotion

```yaml
# .github/workflows/promote.yml
name: Promote to Environment
on:
  workflow_dispatch:
    inputs:
      target_env:
        description: "Target environment"
        required: true
        type: choice
        options: [staging, production]

jobs:
  promote:
    runs-on: ubuntu-latest
    environment: ${{ inputs.target_env }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci

      - name: Smoke test target environment
        env:
          CUSTOMERIO_SITE_ID: ${{ secrets.CIO_SITE_ID }}
          CUSTOMERIO_TRACK_API_KEY: ${{ secrets.CIO_TRACK_API_KEY }}
        run: npx tsx scripts/verify-customerio.ts

      - name: Deploy
        run: echo "Deploy to ${{ inputs.target_env }}"
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Wrong workspace credentials | Config validation throws on startup — check error message |
| Cross-env data leak | Event prefix prevents accidental production triggers |
| Production in dry-run | Config validator explicitly blocks this combination |
| Missing env-specific secret | Kubernetes ExternalSecrets or CI secret scoping |

## Resources

- [Customer.io Workspaces](https://docs.customer.io/accounts-and-workspaces/managing-credentials/)
- [Account Regions](https://docs.customer.io/accounts-and-workspaces/data-centers/)

## Next Steps

After multi-env setup, proceed to `customerio-observability` for monitoring.
