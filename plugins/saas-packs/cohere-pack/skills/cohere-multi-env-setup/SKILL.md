---
name: cohere-multi-env-setup
description: |
  Configure Cohere across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment
  API keys, model selection, and rate limit strategies.
  Trigger with phrases like "cohere environments", "cohere staging",
  "cohere dev prod", "cohere environment setup", "cohere config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Multi-Environment Setup

## Overview
Configure Cohere API v2 across dev/staging/prod with environment-specific API keys, model selection, and budget controls.

## Prerequisites
- Separate Cohere API keys per environment (trial for dev, production for staging/prod)
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- Environment detection in application

## Environment Strategy

| Environment | API Key Type | Model | maxTokens | Caching |
|-------------|-------------|-------|-----------|---------|
| Development | Trial (free) | `command-r7b-12-2024` | 200 | Disabled |
| Staging | Production | `command-r-08-2024` | 1000 | Enabled |
| Production | Production | `command-a-03-2025` | 4096 | Enabled |

## Instructions

### Step 1: Configuration Structure

```typescript
// src/config/cohere.ts
type Environment = 'development' | 'staging' | 'production';

interface CohereEnvConfig {
  chatModel: string;
  embedModel: string;
  rerankModel: string;
  maxTokens: number;
  cacheEnabled: boolean;
  cacheTtlMs: number;
  retries: number;
  timeoutSeconds: number;
}

const configs: Record<Environment, CohereEnvConfig> = {
  development: {
    chatModel: 'command-r7b-12-2024',    // Fastest, cheapest
    embedModel: 'embed-v4.0',
    rerankModel: 'rerank-v3.5',
    maxTokens: 200,                       // Limit for dev
    cacheEnabled: false,                   // See real responses
    cacheTtlMs: 0,
    retries: 1,                            // Fail fast in dev
    timeoutSeconds: 30,
  },
  staging: {
    chatModel: 'command-r-08-2024',       // Mid-tier for testing
    embedModel: 'embed-v4.0',
    rerankModel: 'rerank-v3.5',
    maxTokens: 1000,
    cacheEnabled: true,
    cacheTtlMs: 5 * 60 * 1000,           // 5 minutes
    retries: 3,
    timeoutSeconds: 60,
  },
  production: {
    chatModel: 'command-a-03-2025',       // Best quality
    embedModel: 'embed-v4.0',
    rerankModel: 'rerank-v3.5',
    maxTokens: 4096,
    cacheEnabled: true,
    cacheTtlMs: 15 * 60 * 1000,          // 15 minutes
    retries: 5,
    timeoutSeconds: 120,
  },
};

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV ?? 'development';
  if (['development', 'staging', 'production'].includes(env)) {
    return env as Environment;
  }
  return 'development';
}

export function getCohereConfig(): CohereEnvConfig & { environment: Environment } {
  const env = detectEnvironment();
  return { ...configs[env], environment: env };
}
```

### Step 2: Environment-Aware Client

```typescript
// src/cohere/client.ts
import { CohereClientV2 } from 'cohere-ai';
import { getCohereConfig } from '../config/cohere';

let instance: CohereClientV2 | null = null;

export function getCohere(): CohereClientV2 {
  if (!instance) {
    const config = getCohereConfig();

    if (!process.env.CO_API_KEY) {
      throw new Error(`CO_API_KEY not set for ${config.environment} environment`);
    }

    instance = new CohereClientV2({
      token: process.env.CO_API_KEY,
      timeoutInSeconds: config.timeoutSeconds,
    });

    console.log(`[cohere] Initialized for ${config.environment} (model: ${config.chatModel})`);
  }
  return instance;
}
```

### Step 3: Secret Management

```bash
# --- Local Development ---
# .env.local (git-ignored)
CO_API_KEY=trial-key-for-dev

# --- GitHub Actions (CI) ---
gh secret set CO_API_KEY --body "production-key-for-ci"

# --- AWS Secrets Manager ---
aws secretsmanager create-secret \
  --name cohere/staging/api-key \
  --secret-string "staging-production-key"

aws secretsmanager create-secret \
  --name cohere/production/api-key \
  --secret-string "prod-production-key"

# --- GCP Secret Manager ---
echo -n "staging-key" | gcloud secrets create cohere-api-key-staging --data-file=-
echo -n "prod-key" | gcloud secrets create cohere-api-key-prod --data-file=-

# --- HashiCorp Vault ---
vault kv put secret/cohere/staging api_key="staging-key"
vault kv put secret/cohere/production api_key="prod-key"
```

### Step 4: Environment Guards

```typescript
// Prevent expensive operations in development
function guardExpensiveOperation(operation: string): void {
  const config = getCohereConfig();

  if (config.environment === 'development') {
    // In dev, warn but don't block
    console.warn(`[cohere] ${operation} using trial key — limited to 20 calls/min`);
  }
}

// Prevent development keys in production
function validateKeyForEnv(): void {
  const config = getCohereConfig();
  const key = process.env.CO_API_KEY ?? '';

  if (config.environment === 'production' && key.length < 30) {
    throw new Error('Production requires a production API key (not trial)');
  }
}
```

### Step 5: Per-Environment API Calls

```typescript
import { getCohereConfig } from '../config/cohere';

export async function chat(message: string): Promise<string> {
  const config = getCohereConfig();
  const cohere = getCohere();

  const response = await cohere.chat({
    model: config.chatModel,     // Environment-specific model
    messages: [{ role: 'user', content: message }],
    maxTokens: config.maxTokens, // Environment-specific limit
  });

  return response.message?.content?.[0]?.text ?? '';
}

export async function embed(texts: string[]): Promise<number[][]> {
  const config = getCohereConfig();
  const cohere = getCohere();

  const response = await cohere.embed({
    model: config.embedModel,
    texts,
    inputType: 'search_document',
    embeddingTypes: config.environment === 'development' ? ['float'] : ['int8'], // Cheaper in prod
  });

  return response.embeddings.float ?? response.embeddings.int8;
}
```

### Step 6: Docker Compose for Local Multi-Env Testing

```yaml
# docker-compose.yml
services:
  app-dev:
    build: .
    environment:
      - NODE_ENV=development
      - CO_API_KEY=${CO_API_KEY_DEV}
    ports:
      - "3000:3000"

  app-staging:
    build: .
    environment:
      - NODE_ENV=staging
      - CO_API_KEY=${CO_API_KEY_STAGING}
    ports:
      - "3001:3000"
```

## Output
- Per-environment Cohere configuration (model, tokens, timeout)
- Secret management across dev/staging/prod
- Environment guards preventing misuse
- Docker compose for local multi-env testing

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Trial key in production | Wrong secret | Validate key length at startup |
| Rate limited in dev | Trial key limits | Use 20 calls/min budget |
| Model not found | Typo in config | Validate model IDs at startup |
| Config merge fails | Missing environment | Default to development |

## Resources
- [Cohere API Keys](https://dashboard.cohere.com/api-keys)
- [Cohere Rate Limits](https://docs.cohere.com/docs/rate-limits)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For observability setup, see `cohere-observability`.
