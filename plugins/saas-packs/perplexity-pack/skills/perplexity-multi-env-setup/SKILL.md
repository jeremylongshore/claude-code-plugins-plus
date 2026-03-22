---
name: perplexity-multi-env-setup
description: |
  Configure Perplexity Sonar API across development, staging, and production environments.
  Use when setting up multi-environment search integrations, managing API keys
  per environment, or controlling cost through model routing by env.
  Trigger with phrases like "perplexity environments", "perplexity staging",
  "perplexity dev prod", "perplexity environment config".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, cost-optimization]

---
# Perplexity Multi-Environment Setup

## Overview
Configure Perplexity Sonar API across dev/staging/prod. Key decisions per environment: which models are allowed (sonar vs sonar-pro), rate limits, and cost caps. All environments use the same base URL (`https://api.perplexity.ai`) but different API keys with different budget limits.

## Environment Strategy

| Environment | Model | Rate Limit | Key Source | Monthly Budget |
|-------------|-------|-----------|------------|----------------|
| Development | `sonar` only | 5 RPM self-imposed | `.env.local` | $10 |
| Staging | `sonar` only | 20 RPM | CI secrets | $50 |
| Production | `sonar` + `sonar-pro` | 50 RPM | Secret manager | $500+ |

## Prerequisites
- Separate Perplexity API keys per environment
- `openai` package installed
- Secret management (env files for dev, vault/KMS for prod)

## Instructions

### Step 1: Configuration Structure
```
config/
  perplexity/
    base.ts           # OpenAI client + base URL
    development.ts    # Dev: sonar only, low limits
    staging.ts        # Staging: sonar only, moderate limits
    production.ts     # Prod: full model access
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/perplexity/base.ts
import OpenAI from "openai";

export const PERPLEXITY_BASE_URL = "https://api.perplexity.ai";

export function createPerplexityClient(apiKey: string): OpenAI {
  if (!apiKey) throw new Error("Perplexity API key is required");
  if (!apiKey.startsWith("pplx-")) throw new Error("Invalid Perplexity API key format");

  return new OpenAI({ apiKey, baseURL: PERPLEXITY_BASE_URL });
}
```

### Step 3: Environment Configs
```typescript
// config/perplexity/development.ts
export const devConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY!,
  defaultModel: "sonar" as const,
  deepModel: "sonar" as const,       // No sonar-pro in dev (cost)
  maxTokens: 512,
  maxConcurrentRequests: 1,
  cacheTTLMs: 24 * 3600_000,         // Long cache in dev
};

// config/perplexity/staging.ts
export const stagingConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY_STAGING!,
  defaultModel: "sonar" as const,
  deepModel: "sonar" as const,       // Keep sonar in staging
  maxTokens: 1024,
  maxConcurrentRequests: 2,
  cacheTTLMs: 4 * 3600_000,
};

// config/perplexity/production.ts
export const productionConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY_PROD!,
  defaultModel: "sonar" as const,    // Fast queries use sonar
  deepModel: "sonar-pro" as const,   // Research queries use sonar-pro
  maxTokens: 4096,
  maxConcurrentRequests: 10,
  cacheTTLMs: 1 * 3600_000,          // Shorter cache in prod (freshness)
};
```

### Step 4: Environment Resolver
```typescript
// config/perplexity/index.ts
import { createPerplexityClient } from "./base";
import { devConfig } from "./development";
import { stagingConfig } from "./staging";
import { productionConfig } from "./production";

type SearchDepth = "quick" | "deep";

const configs = {
  development: devConfig,
  staging: stagingConfig,
  production: productionConfig,
};

export function getConfig() {
  const env = process.env.NODE_ENV || "development";
  const config = configs[env as keyof typeof configs];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  if (!config.apiKey) throw new Error(`PERPLEXITY_API_KEY not set for ${env}`);
  return config;
}

export function getClient() {
  return createPerplexityClient(getConfig().apiKey);
}

export function getModelForDepth(depth: SearchDepth): string {
  const cfg = getConfig();
  return depth === "deep" ? cfg.deepModel : cfg.defaultModel;
}
```

### Step 5: Usage with Environment-Aware Search
```typescript
// lib/search.ts
import { getClient, getModelForDepth, getConfig } from "../config/perplexity";

export async function search(query: string, depth: "quick" | "deep" = "quick") {
  const client = getClient();
  const model = getModelForDepth(depth);
  const config = getConfig();

  const result = await client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: "Provide accurate, well-sourced answers." },
      { role: "user", content: query },
    ],
    max_tokens: depth === "deep" ? config.maxTokens : Math.min(512, config.maxTokens),
  });

  return {
    answer: result.choices[0].message.content,
    citations: (result as any).citations || [],
    model,
    environment: process.env.NODE_ENV,
    usage: result.usage,
  };
}
```

### Step 6: Secret Manager Integration (Production)
```bash
set -euo pipefail
# Google Cloud Secret Manager
gcloud secrets create perplexity-api-key-prod \
  --data-file=<(echo -n "$PERPLEXITY_API_KEY_PROD")

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name perplexity/api-key-prod \
  --secret-string "$PERPLEXITY_API_KEY_PROD"

# HashiCorp Vault
vault kv put secret/perplexity api_key="$PERPLEXITY_API_KEY_PROD"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401` in staging | Wrong API key for environment | Verify `PERPLEXITY_API_KEY_STAGING` |
| `429` in dev | Exceeding self-imposed limit | Add request queuing |
| sonar-pro in dev | Config not restricting models | Set `deepModel: "sonar"` in dev config |
| High dev costs | Using production config locally | Ensure `NODE_ENV=development` is set |

## Output
- Environment-specific Perplexity configurations
- Model routing by environment and query depth
- Secret manager integration for production keys
- Cost controls per environment

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Pricing](https://docs.perplexity.ai/docs/getting-started/pricing)

## Next Steps
For deployment configuration, see `perplexity-deploy-integration`.
