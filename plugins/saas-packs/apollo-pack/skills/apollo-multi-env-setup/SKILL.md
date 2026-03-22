---
name: apollo-multi-env-setup
description: |
  Configure Apollo.io multi-environment setup.
  Use when setting up development, staging, and production environments,
  or managing multiple Apollo configurations.
  Trigger with phrases like "apollo environments", "apollo staging",
  "apollo dev prod", "apollo multi-tenant", "apollo env config".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, apollo-multi]

---
# Apollo Multi-Environment Setup

## Overview
Configure Apollo.io for development, staging, and production with isolated API keys, environment-specific rate limits, feature gating, and Kubernetes-native secret management. Apollo provides sandbox tokens for testing that return dummy data without consuming credits.

## Prerequisites
- Separate Apollo API keys per environment (or sandbox tokens for dev)
- Node.js 18+

## Instructions

### Step 1: Environment Configuration Schema
```typescript
// src/config/apollo-config.ts
import { z } from 'zod';

const EnvironmentSchema = z.enum(['development', 'staging', 'production']);

const ApolloEnvConfig = z.object({
  environment: EnvironmentSchema,
  apiKey: z.string().min(10),
  baseUrl: z.string().url().default('https://api.apollo.io/api/v1'),
  isSandbox: z.boolean().default(false),
  rateLimit: z.object({
    maxPerMinute: z.number().min(1),
    concurrency: z.number().min(1).max(20),
  }),
  features: z.object({
    enrichment: z.boolean(),
    sequences: z.boolean(),
    deals: z.boolean(),
    bulkEnrichment: z.boolean(),
  }),
  credits: z.object({
    dailyBudget: z.number(),
    alertThreshold: z.number(),  // percentage
  }),
  logging: z.object({
    level: z.enum(['debug', 'info', 'warn', 'error']),
    redactPII: z.boolean(),
  }),
});

type ApolloEnvConfig = z.infer<typeof ApolloEnvConfig>;
```

### Step 2: Per-Environment Configs
```typescript
const configs: Record<string, ApolloEnvConfig> = {
  development: {
    environment: 'development',
    apiKey: process.env.APOLLO_SANDBOX_KEY ?? process.env.APOLLO_API_KEY_DEV!,
    baseUrl: 'https://api.apollo.io/api/v1',
    isSandbox: true,
    rateLimit: { maxPerMinute: 20, concurrency: 2 },
    features: { enrichment: true, sequences: false, deals: false, bulkEnrichment: false },
    credits: { dailyBudget: 10, alertThreshold: 80 },
    logging: { level: 'debug', redactPII: false },
  },
  staging: {
    environment: 'staging',
    apiKey: process.env.APOLLO_API_KEY_STAGING!,
    baseUrl: 'https://api.apollo.io/api/v1',
    isSandbox: false,
    rateLimit: { maxPerMinute: 50, concurrency: 5 },
    features: { enrichment: true, sequences: true, deals: true, bulkEnrichment: true },
    credits: { dailyBudget: 50, alertThreshold: 70 },
    logging: { level: 'info', redactPII: true },
  },
  production: {
    environment: 'production',
    apiKey: process.env.APOLLO_API_KEY_PROD!,
    baseUrl: 'https://api.apollo.io/api/v1',
    isSandbox: false,
    rateLimit: { maxPerMinute: 100, concurrency: 10 },
    features: { enrichment: true, sequences: true, deals: true, bulkEnrichment: true },
    credits: { dailyBudget: 500, alertThreshold: 90 },
    logging: { level: 'warn', redactPII: true },
  },
};
```

### Step 3: Environment-Aware Client Factory
```typescript
// src/config/client-factory.ts
import axios, { AxiosInstance } from 'axios';

export function createEnvClient(config: ApolloEnvConfig): AxiosInstance {
  const validated = ApolloEnvConfig.parse(config);

  const client = axios.create({
    baseURL: validated.baseUrl,
    headers: { 'Content-Type': 'application/json', 'x-api-key': validated.apiKey },
    timeout: validated.environment === 'development' ? 30_000 : 15_000,
  });

  // Feature gate: block disabled endpoints
  client.interceptors.request.use((req) => {
    if (req.url?.includes('/people/match') && !validated.features.enrichment)
      throw new Error(`Enrichment disabled in ${validated.environment}`);
    if (req.url?.includes('/emailer_campaigns') && !validated.features.sequences)
      throw new Error(`Sequences disabled in ${validated.environment}`);
    if (req.url?.includes('/opportunities') && !validated.features.deals)
      throw new Error(`Deals disabled in ${validated.environment}`);
    if (req.url?.includes('/people/bulk_match') && !validated.features.bulkEnrichment)
      throw new Error(`Bulk enrichment disabled in ${validated.environment}`);
    return req;
  });

  // Debug logging in dev
  if (validated.logging.level === 'debug') {
    client.interceptors.request.use((req) => {
      console.log(`[${validated.environment}] ${req.method?.toUpperCase()} ${req.url}`);
      return req;
    });
  }

  return client;
}

export function getClient(): AxiosInstance {
  const env = process.env.NODE_ENV ?? 'development';
  return createEnvClient(configs[env] ?? configs.development);
}
```

### Step 4: Kubernetes Secrets
```yaml
# k8s/dev/apollo-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: apollo-credentials
  namespace: sales-dev
type: Opaque
stringData:
  APOLLO_SANDBOX_KEY: "sandbox-token-here"
  APOLLO_API_KEY_DEV: "dev-key-here"
---
# k8s/prod/apollo-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: apollo-credentials
  namespace: sales-prod
type: Opaque
stringData:
  APOLLO_API_KEY_PROD: "master-key-here"
```

### Step 5: Environment Verification Script
```typescript
// src/scripts/verify-envs.ts
async function verifyAllEnvironments() {
  for (const [env, config] of Object.entries(configs)) {
    try {
      const client = createEnvClient(config);
      const { data } = await client.get('/auth/health');
      const isMaster = await testMasterAccess(client);
      console.log(`${env}: ${data.is_logged_in ? 'OK' : 'FAIL'} (${isMaster ? 'master' : 'standard'} key, sandbox: ${config.isSandbox})`);
    } catch (err: any) {
      console.error(`${env}: FAIL — ${err.message}`);
    }
  }
}

async function testMasterAccess(client: AxiosInstance): Promise<boolean> {
  try { await client.post('/contacts/search', { per_page: 1 }); return true; }
  catch { return false; }
}
```

## Output
- Zod-validated environment config schema with feature flags and credit budgets
- Three environment configs (dev with sandbox, staging, production)
- Client factory with feature gating and debug logging
- Kubernetes secrets per namespace
- Environment verification script testing all configs

## Error Handling
| Issue | Resolution |
|-------|------------|
| Feature disabled | Client throws descriptive error identifying which env blocked it |
| Wrong environment | Check `NODE_ENV`, client falls back to development |
| Missing API key | Zod throws with clear validation error |
| Sandbox returning dummy data | Expected in development — use staging for real data testing |

## Resources
- [Apollo Sandbox Testing](https://docs.apollo.io/docs/test-api-key)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)
- [12-Factor App Config](https://12factor.net/config)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Steps
Proceed to `apollo-observability` for monitoring setup.
