---
name: fireflies-multi-env-setup
description: |
  Configure Fireflies.ai across dev, staging, and production with isolated API keys.
  Use when setting up multi-environment deployments, managing per-env secrets,
  or implementing environment-specific Fireflies configurations.
  Trigger with phrases like "fireflies environments", "fireflies staging",
  "fireflies dev prod", "fireflies environment setup", "fireflies config by env".
allowed-tools: Read, Write, Edit, Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, deployment]

---
# Fireflies.ai Multi-Environment Setup

## Overview
Configure Fireflies.ai with isolated API keys, webhook URLs, and settings per environment. Each environment gets its own Fireflies workspace or API key to prevent cross-environment data leakage.

## Environment Strategy

| Environment | API Key | Webhook URL | Settings |
|-------------|---------|-------------|----------|
| Development | `FIREFLIES_API_KEY_DEV` | localhost (ngrok) | Debug logs, no cache |
| Staging | `FIREFLIES_API_KEY_STAGING` | staging.app.com/webhooks | Prod-like, short cache |
| Production | `FIREFLIES_API_KEY_PROD` | app.com/webhooks | Hardened, long cache |

## Instructions

### Step 1: Environment Configuration Module
```typescript
// config/fireflies.ts
interface FirefliesConfig {
  apiKey: string;
  apiUrl: string;
  webhookSecret: string;
  cache: { enabled: boolean; ttlSeconds: number };
  debug: boolean;
  timeout: number;
  maxRetries: number;
}

const configs: Record<string, Partial<FirefliesConfig>> = {
  development: {
    apiKey: process.env.FIREFLIES_API_KEY_DEV || "",
    webhookSecret: process.env.FIREFLIES_WEBHOOK_SECRET_DEV || "dev-secret-16char",
    cache: { enabled: false, ttlSeconds: 60 },
    debug: true,
    timeout: 30000,
    maxRetries: 1,
  },
  staging: {
    apiKey: process.env.FIREFLIES_API_KEY_STAGING || "",
    webhookSecret: process.env.FIREFLIES_WEBHOOK_SECRET_STAGING || "",
    cache: { enabled: true, ttlSeconds: 300 },
    debug: false,
    timeout: 15000,
    maxRetries: 3,
  },
  production: {
    apiKey: process.env.FIREFLIES_API_KEY_PROD || "",
    webhookSecret: process.env.FIREFLIES_WEBHOOK_SECRET_PROD || "",
    cache: { enabled: true, ttlSeconds: 3600 },
    debug: false,
    timeout: 10000,
    maxRetries: 5,
  },
};

function detectEnvironment(): string {
  if (process.env.NODE_ENV === "production") return "production";
  if (process.env.NODE_ENV === "staging" || process.env.VERCEL_ENV === "preview") return "staging";
  return "development";
}

export function getFirefliesConfig(): FirefliesConfig {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config?.apiKey) {
    throw new Error(`FIREFLIES_API_KEY not configured for environment: ${env}`);
  }

  return {
    apiUrl: "https://api.fireflies.ai/graphql",
    ...config,
  } as FirefliesConfig;
}
```

### Step 2: Environment-Aware Client
```typescript
// lib/fireflies-client.ts
import { getFirefliesConfig } from "../config/fireflies";

export function createFirefliesClient() {
  const config = getFirefliesConfig();

  return {
    async query(gql: string, variables?: Record<string, any>) {
      if (config.debug) {
        console.log(`[Fireflies:${detectEnvironment()}] Query:`, gql.slice(0, 100));
      }

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), config.timeout);

      try {
        const res = await fetch(config.apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${config.apiKey}`,
          },
          body: JSON.stringify({ query: gql, variables }),
          signal: controller.signal,
        });

        const json = await res.json();
        if (json.errors) throw new Error(json.errors[0].message);
        return json.data;
      } finally {
        clearTimeout(timeout);
      }
    },

    getConfig() {
      return { environment: detectEnvironment(), ...config, apiKey: "[REDACTED]" };
    },
  };
}
```

### Step 3: Secret Management by Platform

**Local Development:**
```bash
# .env.local (git-ignored)
FIREFLIES_API_KEY_DEV=your-dev-key
FIREFLIES_WEBHOOK_SECRET_DEV=your-dev-secret-16ch
```

**GitHub Actions:**
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      FIREFLIES_API_KEY_STAGING: ${{ secrets.FIREFLIES_API_KEY_STAGING }}
      FIREFLIES_WEBHOOK_SECRET_STAGING: ${{ secrets.FIREFLIES_WEBHOOK_SECRET_STAGING }}

  deploy-production:
    environment: production
    needs: deploy-staging
    env:
      FIREFLIES_API_KEY_PROD: ${{ secrets.FIREFLIES_API_KEY_PROD }}
      FIREFLIES_WEBHOOK_SECRET_PROD: ${{ secrets.FIREFLIES_WEBHOOK_SECRET_PROD }}
```

**GCP Secret Manager:**
```bash
set -euo pipefail
# Store secrets
echo -n "your-prod-key" | gcloud secrets create fireflies-api-key-prod --data-file=-
echo -n "your-webhook-secret" | gcloud secrets create fireflies-webhook-secret-prod --data-file=-

# Grant access to Cloud Run service
gcloud secrets add-iam-policy-binding fireflies-api-key-prod \
  --member="serviceAccount:your-sa@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 4: Startup Validation
```typescript
import { z } from "zod";

const FirefliesConfigSchema = z.object({
  apiKey: z.string().min(10, "API key too short"),
  apiUrl: z.string().url(),
  webhookSecret: z.string().min(16, "Webhook secret must be 16+ chars"),
  timeout: z.number().positive(),
});

// Validate on startup -- fail fast
export function validateConfig() {
  const config = getFirefliesConfig();
  const result = FirefliesConfigSchema.safeParse(config);

  if (!result.success) {
    console.error("Fireflies config validation failed:");
    for (const issue of result.error.issues) {
      console.error(`  ${issue.path.join(".")}: ${issue.message}`);
    }
    process.exit(1);
  }

  console.log(`Fireflies config valid for ${detectEnvironment()}`);
}
```

### Step 5: Per-Environment Webhook Registration
Each environment needs its own webhook URL registered in Fireflies:
- **Dev:** Use ngrok or similar for local testing
- **Staging:** `https://staging.yourapp.com/api/webhooks/fireflies`
- **Production:** `https://yourapp.com/api/webhooks/fireflies`

Register each in the corresponding Fireflies workspace at app.fireflies.ai/settings > Developer settings.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment detected | Missing `NODE_ENV` | Set in deployment platform |
| Secret not found | Wrong env var name | Check naming convention per platform |
| Cross-env data leak | Shared API key | Use separate Fireflies workspaces |
| Startup crash | Missing config | Zod validation catches at boot |

## Output
- Environment-aware Fireflies configuration with type safety
- Secret management across local, CI, and cloud platforms
- Startup validation preventing misconfigured deployments
- Per-environment webhook URL strategy

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps
For deployment, see `fireflies-deploy-integration`.
