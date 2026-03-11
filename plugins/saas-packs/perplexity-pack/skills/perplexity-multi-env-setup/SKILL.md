---
name: perplexity-multi-env-setup
description: |
  Configure Perplexity Sonar API across development, staging, and production environments.
  Use when setting up multi-environment search integrations, managing model selection
  per environment, or controlling cost through sonar vs sonar-pro routing by env.
  Trigger with phrases like "perplexity environments", "perplexity staging",
  "perplexity dev prod", "perplexity environment setup", "perplexity model by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Multi-Environment Setup

## Overview
Perplexity's OpenAI-compatible API uses the base URL `https://api.perplexity.ai`. The key per-environment configuration decisions are model selection and request limits.

## Prerequisites
- Perplexity API key from perplexity.ai/settings/api
- OpenAI-compatible client library (`openai` npm package or equivalent)
- Understanding of Sonar model tiers and their cost tradeoffs

## Environment Strategy

| Environment | Model | Cost/1K requests | Rate Limit | Key Source |
|-------------|-------|-----------------|------------|------------|
| Development | `sonar` | ~$1 | 5 RPM (free tier) | `.env.local` |
| Staging | `sonar` | ~$1 | 5-20 RPM | CI/CD secrets |
| Production | `sonar-pro` (deep), `sonar` (quick) | $1-$5 | 50+ RPM | Secret manager |

## Instructions

### Step 1: Configuration Structure
```
config/
  perplexity/
    base.ts           # OpenAI client pointing to Perplexity
    development.ts    # Dev: sonar model, low rate limit
    staging.ts        # Staging: sonar model, moderate limits
    production.ts     # Prod: sonar-pro for deep queries, sonar for quick
    index.ts          # Environment resolver + model router
```

### Step 2: Base Configuration with OpenAI SDK
```typescript
// config/perplexity/base.ts
import OpenAI from "openai";

export const PERPLEXITY_BASE_URL = "https://api.perplexity.ai";

export function createPerplexityClient(apiKey: string): OpenAI {
  return new OpenAI({
    apiKey,
    baseURL: PERPLEXITY_BASE_URL,
  });
}
```

### Step 3: Environment-Specific Configs
```typescript
// config/perplexity/development.ts
export const devConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY!,
  defaultModel: "sonar",          // always use cheapest model in dev
  deepModel: "sonar",             // no sonar-pro in dev (cost)
  maxTokens: 512,  # 512 bytes
  maxConcurrentRequests: 1,       // stay within free tier 5 RPM
};

// config/perplexity/staging.ts
export const stagingConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY_STAGING!,
  defaultModel: "sonar",
  deepModel: "sonar",             // keep sonar in staging to test cost behavior
  maxTokens: 1024,  # 1024: 1 KB
  maxConcurrentRequests: 2,
};

// config/perplexity/production.ts
export const productionConfig = {
  apiKey: process.env.PERPLEXITY_API_KEY_PROD!,
  defaultModel: "sonar",          // fast queries use sonar
  deepModel: "sonar-pro",         // research queries use sonar-pro
  maxTokens: 4096,  # 4096: 4 KB
  maxConcurrentRequests: 10,
};
```

### Step 4: Environment Resolver with Model Router
```typescript
// config/perplexity/index.ts
import { createPerplexityClient } from "./base";

type SearchDepth = "quick" | "deep";

export function getPerplexityConfig() {
  const env = process.env.NODE_ENV || "development";
  const configs = { development: devConfig, staging: stagingConfig, production: productionConfig };
  const config = configs[env as keyof typeof configs] || devConfig;

  if (!config.apiKey) {
    throw new Error(`PERPLEXITY_API_KEY not set for ${env}`);
  }

  return config;
}

export function getPerplexityClient() {
  const cfg = getPerplexityConfig();
  return createPerplexityClient(cfg.apiKey);
}

export function getModelForDepth(depth: SearchDepth): string {
  const cfg = getPerplexityConfig();
  return depth === "deep" ? cfg.deepModel : cfg.defaultModel;
}
```

### Step 5: Usage with Environment-Aware Model Selection
```typescript
// lib/search.ts
import { getPerplexityClient, getModelForDepth } from "../config/perplexity";

export async function search(query: string, depth: "quick" | "deep" = "quick") {
  const client = getPerplexityClient();
  const model = getModelForDepth(depth);

  const result = await client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: "Provide accurate, well-sourced answers." },
      { role: "user", content: query },
    ],
    max_tokens: depth === "deep" ? 2048 : 512,  # 512: 2048: 2 KB
  });

  return {
    answer: result.choices[0].message.content,
    model,
    usage: result.usage,
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Wrong API key for environment | Verify `PERPLEXITY_API_KEY` in `.env.local` |
| `429 Too Many Requests` | Exceeding 5 RPM on free tier | Add request queuing or upgrade to paid plan |
| `sonar-pro` errors in staging | Config sending deep queries to sonar-pro | Set `deepModel: "sonar"` in staging config |
| High costs in dev | Using sonar-pro accidentally | Hardcode `defaultModel: "sonar"` in dev config |

## Examples

### Verify Which Model Is Active Per Environment
```typescript
import { getModelForDepth, getPerplexityConfig } from "./config/perplexity";

const cfg = getPerplexityConfig();
console.log(`Default model: ${cfg.defaultModel}`);
console.log(`Deep search model: ${cfg.deepModel}`);
console.log(`Max concurrent: ${cfg.maxConcurrentRequests}`);
```

### Cost Estimate Before Production Deploy
```bash
# Estimate cost: 10K quick queries/day at $1/1K = $10/day
# Estimate cost: 1K deep queries/day at $5/1K = $5/day
echo "Estimated daily cost: $15"
```

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Models and Pricing](https://docs.perplexity.ai/guides/model-cards)
- [Perplexity Rate Limits](https://docs.perplexity.ai/guides/rate-limits)

## Next Steps
For deployment configuration, see `perplexity-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale