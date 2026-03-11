---
name: groq-multi-env-setup
description: |
  Configure Groq LLM API across development, staging, and production environments.
  Use when setting up multi-environment deployments with Groq, managing model
  selection per environment, or implementing rate-limit-aware config management.
  Trigger with phrases like "groq environments", "groq staging", "groq dev prod",
  "groq environment setup", "groq multi-env", "groq model config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Groq Multi-Environment Setup

## Overview
Configure Groq across environments with the right balance of cost, speed, and capability per tier. Groq's key differentiator is inference speed (100-300 tokens/second), but rate limits differ dramatically by plan: free tier is 30 RPM / 14,400 RPD for llama-3.1-70b, while paid tier removes most limits. Development typically uses smaller/faster models (llama-3.1-8b) to minimize cost; production uses appropriately-sized models with retry logic for rate limits.

## Prerequisites
- Groq API key(s) per environment from console.groq.com
- Environment variable management (`.env.local`, GitHub Secrets, or cloud secret manager)
- Understanding of Groq's model tiers and rate limits

## Environment Strategy

| Environment | Model | Rate Limit Risk | Config Source |
|-------------|-------|-----------------|---------------|
| Development | `llama-3.1-8b-instant` | Low (small model) | `.env.local` |
| Staging | `llama-3.1-70b-versatile` | Medium | CI/CD secrets |
| Production | `llama-3.1-70b-versatile` or `llama-3.3-70b-specdec` | Managed with retry | Secret manager |

## Instructions

### Step 1: Configuration Structure
```
config/
  groq/
    base.ts           # Shared Groq client setup
    development.ts    # Dev: fast small models, verbose logging
    staging.ts        # Staging: production models, test rate limits
    production.ts     # Prod: hardened retry, error handling
    index.ts          # Environment resolver
```

### Step 2: Base Configuration with Groq SDK
```typescript
// config/groq/base.ts
import Groq from "groq-sdk";

export const BASE_GROQ_CONFIG = {
  maxRetries: 3,
  timeout: 30000,
};
```

### Step 3: Environment-Specific Configs
```typescript
// config/groq/development.ts
export const devConfig = {
  ...BASE_GROQ_CONFIG,
  apiKey: process.env.GROQ_API_KEY,
  model: "llama-3.1-8b-instant",      // fastest, cheapest for dev iteration
  maxTokens: 1024,
  temperature: 0.7,
  logRequests: true,                   // verbose logging in dev
};

// config/groq/staging.ts
export const stagingConfig = {
  ...BASE_GROQ_CONFIG,
  apiKey: process.env.GROQ_API_KEY_STAGING,
  model: "llama-3.1-70b-versatile",   // match production model
  maxTokens: 4096,
  temperature: 0.3,
  logRequests: false,
};

// config/groq/production.ts
export const productionConfig = {
  ...BASE_GROQ_CONFIG,
  apiKey: process.env.GROQ_API_KEY_PROD,
  model: "llama-3.1-70b-versatile",   // or llama-3.3-70b-specdec for faster
  maxTokens: 4096,
  temperature: 0.3,
  maxRetries: 5,                       // more retries for production reliability
  logRequests: false,
};
```

### Step 4: Environment Resolver with Groq Client
```typescript
// config/groq/index.ts
import Groq from "groq-sdk";

type Env = "development" | "staging" | "production";

function detectEnvironment(): Env {
  const env = process.env.NODE_ENV || "development";
  if (env === "production") return "production";
  if (env === "staging") return "staging";
  return "development";
}

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (_client) return _client;

  const env = detectEnvironment();
  const configs = { development: devConfig, staging: stagingConfig, production: productionConfig };
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`GROQ_API_KEY not configured for ${env} environment`);
  }

  _client = new Groq({
    apiKey: config.apiKey,
    maxRetries: config.maxRetries,
    timeout: config.timeout,
  });

  return _client;
}

export function getModelConfig() {
  const env = detectEnvironment();
  const configs = { development: devConfig, staging: stagingConfig, production: productionConfig };
  return configs[env];
}
```

### Step 5: Usage with Rate Limit Handling
```typescript
// lib/groq-service.ts
import { getGroqClient, getModelConfig } from "../config/groq";

export async function complete(prompt: string): Promise<string> {
  const groq = getGroqClient();
  const { model, maxTokens, temperature } = getModelConfig();

  try {
    const completion = await groq.chat.completions.create({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: maxTokens,
      temperature,
    });
    return completion.choices[0].message.content || "";
  } catch (err: any) {
    if (err.status === 429) {
      const retryAfter = parseInt(err.headers?.["retry-after"] || "10");
      console.warn(`Groq rate limited. Retry after ${retryAfter}s`);
      throw new Error(`Rate limited on model ${model}. Retry after ${retryAfter}s`);
    }
    throw err;
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key for environment | Verify `GROQ_API_KEY` in secret manager |
| `429 rate_limit_exceeded` | Free tier limit hit | Switch to paid plan or implement request queuing |
| Model not found | Deprecated model ID | Check console.groq.com/docs/models for current list |
| Slow responses in dev | Using 70b model for iteration | Switch dev config to `llama-3.1-8b-instant` |

## Examples

### Check Which Config Is Active
```typescript
import { getModelConfig } from "./config/groq";

const cfg = getModelConfig();
console.log(`Model: ${cfg.model}, max_tokens: ${cfg.maxTokens}`);
```

### Test Rate Limits Per Environment
```bash
# Quick check: what's my current rate limit status?
curl -s "https://api.groq.com/openai/v1/models" \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq '.data[].id'
```

## Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models Reference](https://console.groq.com/docs/models)
- [Groq Rate Limits by Tier](https://console.groq.com/docs/rate-limits)

## Next Steps
For deployment configuration, see `groq-deploy-integration`.
