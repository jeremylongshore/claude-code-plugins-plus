---
name: instantly-multi-env-setup
description: |
  Configure Instantly.ai across development, staging, and production environments.
  Use when setting up multi-workspace deployments, isolating test from production,
  or managing per-environment API keys and webhook endpoints.
  Trigger with phrases like "instantly environments", "instantly staging",
  "instantly dev prod", "instantly multi-env", "instantly workspace isolation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, multi-environment, configuration]

---
# Instantly Multi-Environment Setup

## Overview
Configure Instantly API v2 integrations across development, staging, and production environments. Instantly uses workspace-level isolation — each workspace has its own accounts, campaigns, leads, and API keys. This skill covers workspace separation, environment-specific configuration, mock server for dev, and safe promotion workflows.

## Environment Strategy

| Environment | Instantly Backend | API Keys | Webhooks | Purpose |
|-------------|------------------|----------|----------|---------|
| Development | Mock server | `mock-key` | localhost:3000 | Code iteration |
| Staging | Separate workspace | Staging key | staging.yourapp.com | Integration testing |
| Production | Production workspace | Prod key | prod.yourapp.com | Live outreach |

## Instructions

### Step 1: Environment Configuration
```typescript
// src/config.ts
import "dotenv/config";

type Env = "development" | "staging" | "production";

interface InstantlyConfig {
  env: Env;
  apiKey: string;
  baseUrl: string;
  webhookSecret: string;
  useMock: boolean;
  dailyLimitCap: number;
  enableRealSending: boolean;
}

export function getConfig(): InstantlyConfig {
  const env = (process.env.NODE_ENV || "development") as Env;

  const configs: Record<Env, InstantlyConfig> = {
    development: {
      env: "development",
      apiKey: process.env.INSTANTLY_API_KEY_DEV || "mock-key",
      baseUrl: "https://developer.instantly.ai/_mock/api/v2",
      webhookSecret: "dev-secret",
      useMock: true,
      dailyLimitCap: 5,
      enableRealSending: false,
    },
    staging: {
      env: "staging",
      apiKey: process.env.INSTANTLY_API_KEY_STAGING || "",
      baseUrl: "https://api.instantly.ai/api/v2",
      webhookSecret: process.env.INSTANTLY_WEBHOOK_SECRET_STAGING || "",
      useMock: false,
      dailyLimitCap: 10,
      enableRealSending: true,
    },
    production: {
      env: "production",
      apiKey: process.env.INSTANTLY_API_KEY_PROD || "",
      baseUrl: "https://api.instantly.ai/api/v2",
      webhookSecret: process.env.INSTANTLY_WEBHOOK_SECRET_PROD || "",
      useMock: false,
      dailyLimitCap: 100,
      enableRealSending: true,
    },
  };

  const config = configs[env];
  if (!config.useMock && !config.apiKey) {
    throw new Error(`INSTANTLY_API_KEY_${env.toUpperCase()} is required for ${env}`);
  }

  return config;
}
```

### Step 2: Environment-Specific .env Files
```bash
# .env.development
NODE_ENV=development
INSTANTLY_API_KEY_DEV=mock-key
INSTANTLY_BASE_URL=https://developer.instantly.ai/_mock/api/v2
INSTANTLY_WEBHOOK_SECRET=dev-secret-123

# .env.staging
NODE_ENV=staging
INSTANTLY_API_KEY_STAGING=your-staging-workspace-key
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v2
INSTANTLY_WEBHOOK_SECRET_STAGING=staging-secret-456

# .env.production
NODE_ENV=production
INSTANTLY_API_KEY_PROD=your-production-workspace-key
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v2
INSTANTLY_WEBHOOK_SECRET_PROD=prod-secret-789
```

### Step 3: Safe Campaign Creation with Environment Guards
```typescript
import { getConfig } from "./config";
import { InstantlyClient } from "./instantly/client";

const config = getConfig();
const client = new InstantlyClient(config.apiKey, config.baseUrl);

async function createCampaignSafe(name: string, sequences: any[]) {
  // Guard: add environment prefix to campaign names
  const envPrefix = config.env === "production" ? "" : `[${config.env.toUpperCase()}] `;
  const safeName = `${envPrefix}${name}`;

  // Guard: cap daily limit per environment
  const campaign = await client.campaigns.create({
    name: safeName,
    daily_limit: Math.min(50, config.dailyLimitCap),
    sequences,
    campaign_schedule: {
      start_date: new Date().toISOString().split("T")[0],
      schedules: [{
        name: "Business Hours",
        timing: { from: "09:00", to: "17:00" },
        days: { "1": true, "2": true, "3": true, "4": true, "5": true, "0": false, "6": false },
        timezone: "America/New_York",
      }],
    },
    stop_on_reply: true,
  });

  console.log(`[${config.env}] Campaign created: ${campaign.name} (${campaign.id})`);

  // Guard: never auto-activate in production
  if (config.env !== "production") {
    await client.campaigns.activate(campaign.id);
    console.log(`[${config.env}] Campaign auto-activated (non-prod)`);
  } else {
    console.log(`[production] Campaign created in DRAFT — manual activation required`);
  }

  return campaign;
}
```

### Step 4: Workspace Isolation Verification
```typescript
async function verifyWorkspaceIsolation() {
  const config = getConfig();

  // Get current workspace info
  const workspace = await client.request<{
    id: string; name: string;
  }>("/workspaces/current");

  console.log(`Environment: ${config.env}`);
  console.log(`Workspace: ${workspace.name} (${workspace.id})`);

  // Safety check: verify workspace matches expected environment
  const expectedWorkspaceNames: Record<string, string[]> = {
    development: ["dev", "test", "mock"],
    staging: ["staging", "stage", "qa"],
    production: ["prod", "production", "live"],
  };

  const expected = expectedWorkspaceNames[config.env] || [];
  const nameMatch = expected.some((n) =>
    workspace.name.toLowerCase().includes(n)
  );

  if (!nameMatch && config.env !== "development") {
    console.warn(`WARNING: Workspace name "${workspace.name}" doesn't match expected ${config.env} pattern`);
    console.warn("Verify you're using the correct API key for this environment");
  }

  // List accounts to verify correct workspace
  const accounts = await client.accounts.list(5);
  console.log(`Accounts in workspace: ${accounts.length}`);
}
```

### Step 5: Webhook Registration Per Environment
```typescript
async function setupWebhooksForEnv() {
  const config = getConfig();

  const webhookBaseUrls: Record<string, string> = {
    development: "http://localhost:3000",
    staging: "https://staging-webhooks.yourapp.com",
    production: "https://webhooks.yourapp.com",
  };

  const baseUrl = webhookBaseUrls[config.env];

  // Clean up existing webhooks
  const existing = await client.webhooks.list();
  for (const w of existing) {
    if (w.name.startsWith(`[${config.env}]`)) {
      await client.webhooks.delete(w.id);
    }
  }

  // Register environment-specific webhooks
  const events = ["reply_received", "email_bounced", "lead_interested", "lead_meeting_booked"];

  for (const event of events) {
    await client.webhooks.create({
      name: `[${config.env}] ${event}`,
      target_hook_url: `${baseUrl}/webhooks/instantly`,
      event_type: event,
      headers: { "X-Webhook-Secret": config.webhookSecret },
    });
  }

  console.log(`[${config.env}] Registered ${events.length} webhooks -> ${baseUrl}`);
}
```

## Promotion Workflow
```
Development (mock)  →  Staging (real API, test data)  →  Production (live)
    |                        |                               |
    |  Code changes          |  Integration test             |  Manual activation
    |  Unit tests            |  Small lead list (10)         |  Full lead list
    |  Mock server           |  Staging workspace            |  Production workspace
    |                        |  Webhook verification         |  Monitoring + alerts
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong workspace | API key mismatch | Run `verifyWorkspaceIsolation()` |
| Prod campaign auto-launched | Missing environment guard | Add `if (env !== "production")` check |
| Webhook pointing to wrong env | Stale webhook registration | Re-run `setupWebhooksForEnv()` |
| Staging data in production | Cross-env contamination | Use separate workspaces with separate API keys |

## Resources
- [Instantly Workspaces](https://developer.instantly.ai/api/v2/schemas)
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Mock Server](https://developer.instantly.ai/_mock/api/v2/)

## Next Steps
For observability and monitoring, see `instantly-observability`.
