---
name: groq-multi-env-setup
description: |
  Configure Groq across dev, staging, and production with environment-specific
  model selection, rate limits, and API keys.
  Trigger with phrases like "groq environments", "groq staging", "groq dev prod",
  "groq environment setup", "groq multi-env", "groq config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, deployment, api, llm]

---
# Groq Multi-Environment Setup

## Overview
Configure Groq API access across development, staging, and production with the right model, rate limit strategy, and secret management per environment. Key insight: use `llama-3.1-8b-instant` in development (cheapest, fastest), match production model in staging, and harden production with retries and fallbacks.

## Environment Strategy

| Environment | API Key Source | Default Model | Retry | Logging |
|-------------|---------------|---------------|-------|---------|
| Development | `.env.local` | `llama-3.1-8b-instant` | 1 | Verbose |
| Staging | CI/CD secrets | `llama-3.3-70b-versatile` | 3 | Standard |
| Production | Secret manager | `llama-3.3-70b-versatile` | 5 | Structured |

## Instructions

### Step 1: Configuration Module
```typescript
// config/groq.ts
import Groq from "groq-sdk";

interface GroqEnvConfig {
  apiKey: string;
  model: string;
  maxTokens: number;
  temperature: number;
  maxRetries: number;
  timeout: number;
  logRequests: boolean;
}

const configs: Record<string, GroqEnvConfig> = {
  development: {
    apiKey: process.env.GROQ_API_KEY || "",
    model: "llama-3.1-8b-instant",       // Cheapest, fastest for iteration
    maxTokens: 512,
    temperature: 0.7,
    maxRetries: 1,
    timeout: 15_000,
    logRequests: true,                     // Verbose in dev
  },
  staging: {
    apiKey: process.env.GROQ_API_KEY_STAGING || process.env.GROQ_API_KEY || "",
    model: "llama-3.3-70b-versatile",    // Match production model
    maxTokens: 2048,
    temperature: 0.3,
    maxRetries: 3,
    timeout: 30_000,
    logRequests: false,
  },
  production: {
    apiKey: process.env.GROQ_API_KEY_PROD || process.env.GROQ_API_KEY || "",
    model: "llama-3.3-70b-versatile",    // Quality model
    maxTokens: 2048,
    temperature: 0.3,
    maxRetries: 5,                        // More retries in prod
    timeout: 30_000,
    logRequests: false,
  },
};

function getEnv(): string {
  return process.env.NODE_ENV || "development";
}

export function getGroqConfig(): GroqEnvConfig {
  const env = getEnv();
  const config = configs[env] || configs.development;

  if (!config.apiKey) {
    throw new Error(
      `GROQ_API_KEY not set for ${env}. ` +
      (env === "development"
        ? "Copy .env.example to .env.local and add your key from console.groq.com/keys"
        : `Set GROQ_API_KEY_${env.toUpperCase()} in your secret manager`)
    );
  }

  return config;
}

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (!_client) {
    const config = getGroqConfig();
    _client = new Groq({
      apiKey: config.apiKey,
      maxRetries: config.maxRetries,
      timeout: config.timeout,
    });
  }
  return _client;
}
```

### Step 2: Environment-Aware Service
```typescript
// services/groq-service.ts
import { getGroqClient, getGroqConfig } from "../config/groq";

export async function complete(
  messages: any[],
  options?: { model?: string; maxTokens?: number }
): Promise<string> {
  const groq = getGroqClient();
  const config = getGroqConfig();

  const model = options?.model || config.model;
  const maxTokens = options?.maxTokens || config.maxTokens;

  if (config.logRequests) {
    console.log(`[groq:${model}] ${messages.length} messages, max_tokens=${maxTokens}`);
  }

  try {
    const completion = await groq.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
      temperature: config.temperature,
    });

    if (config.logRequests) {
      const u = completion.usage!;
      console.log(`[groq:${model}] ${u.prompt_tokens}+${u.completion_tokens} tokens, ${((u as any).total_time * 1000).toFixed(0)}ms`);
    }

    return completion.choices[0].message.content || "";
  } catch (err: any) {
    if (err.status === 429) {
      const retryAfter = err.headers?.["retry-after"] || "?";
      console.error(`[groq:${model}] Rate limited. Retry after ${retryAfter}s`);
    }
    throw err;
  }
}
```

### Step 3: Secret Management by Platform
```bash
set -euo pipefail

# === Development ===
# .env.local (git-ignored)
cat > .env.example << 'EOF'
# Get your API key at https://console.groq.com/keys
GROQ_API_KEY=gsk_your_dev_key_here
EOF

# === Staging (GitHub Actions) ===
gh secret set GROQ_API_KEY_STAGING --body "gsk_staging_key"

# === Production (Cloud Platforms) ===
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name groq/prod/api-key \
  --secret-string "gsk_prod_key"

# GCP Secret Manager
echo -n "gsk_prod_key" | gcloud secrets create groq-api-key-prod --data-file=-

# HashiCorp Vault
vault kv put secret/groq/prod api_key="gsk_prod_key"
```

### Step 4: Docker Compose Multi-Env
```yaml
# docker-compose.yml
services:
  app-dev:
    build: .
    environment:
      - NODE_ENV=development
      - GROQ_API_KEY=${GROQ_API_KEY}
    profiles: ["dev"]

  app-staging:
    build: .
    environment:
      - NODE_ENV=staging
      - GROQ_API_KEY=${GROQ_API_KEY_STAGING}
    profiles: ["staging"]

  app-prod:
    build: .
    environment:
      - NODE_ENV=production
    secrets:
      - groq_api_key
    profiles: ["prod"]

secrets:
  groq_api_key:
    external: true
```

### Step 5: Verify Environment Config
```typescript
// scripts/verify-groq-env.ts
import { getGroqConfig, getGroqClient } from "../config/groq";

async function verify() {
  const config = getGroqConfig();
  console.log(`Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(`Model: ${config.model}`);
  console.log(`Max retries: ${config.maxRetries}`);
  console.log(`API key prefix: ${config.apiKey.slice(0, 8)}...`);

  const groq = getGroqClient();
  const start = performance.now();
  const result = await groq.chat.completions.create({
    model: config.model,
    messages: [{ role: "user", content: "Reply: OK" }],
    max_tokens: 5,
    temperature: 0,
  });

  console.log(`Connection: OK (${Math.round(performance.now() - start)}ms)`);
  console.log(`Model response: ${result.choices[0].message.content}`);
}

verify().catch((err) => {
  console.error(`FAILED: ${err.message}`);
  process.exit(1);
});
```

### Step 6: Rate Limit Awareness by Environment
```bash
set -euo pipefail
# Check current rate limits for your key
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^x-ratelimit"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `GROQ_API_KEY not set` | Missing env var | Check .env.local (dev) or secret manager (prod) |
| Wrong model in env | Config mismatch | Verify with `verify-groq-env.ts` script |
| Rate limited in dev | Free tier limits | Use `llama-3.1-8b-instant` with low max_tokens |
| Staging/prod key in dev | Key leak risk | Use separate Groq organizations per environment |

## Resources
- [Groq Console](https://console.groq.com)
- [Groq API Keys](https://console.groq.com/keys)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)

## Next Steps
For deployment configuration, see `groq-deploy-integration`.
