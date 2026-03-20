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
---
# Apollo Multi-Environment Setup

## Overview
Configure Apollo.io for multiple environments (development, staging, production) with isolated API keys, environment-specific rate limits, configuration validation, and Kubernetes-native secret management.

## Prerequisites
- Valid Apollo.io API credentials (separate keys per environment)
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Define Environment Configuration Schema
```typescript
// src/config/apollo-config.ts
import { z } from 'zod';

const EnvironmentSchema = z.enum(['development', 'staging', 'production']);

const ApolloEnvConfigSchema = z.object({
  environment: EnvironmentSchema,
  apiKey: z.string().min(10),
  baseUrl: z.string().url().default('https://api.apollo.io/v1'),
  rateLimit: z.object({
    maxPerHour: z.number().min(1),
    concurrency: z.number().min(1).max(20),
  }),
  features: z.object({
    enrichment: z.boolean(),
    sequences: z.boolean(),
    webhooks: z.boolean(),
  }),
  logging: z.object({
    level: z.enum(['debug', 'info', 'warn', 'error']),
    redactPII: z.boolean(),
  }),
});

type ApolloEnvConfig = z.infer<typeof ApolloEnvConfigSchema>;
```

### Step 2: Create Per-Environment Configuration Files
```typescript
// config/development.ts
export const developmentConfig: ApolloEnvConfig = {
  environment: 'development',
  apiKey: process.env.APOLLO_API_KEY_DEV!,
  baseUrl: 'https://api.apollo.io/v1',
  rateLimit: { maxPerHour: 50, concurrency: 2 },
  features: { enrichment: true, sequences: false, webhooks: false },
  logging: { level: 'debug', redactPII: false },
};

// config/staging.ts
export const stagingConfig: ApolloEnvConfig = {
  environment: 'staging',
  apiKey: process.env.APOLLO_API_KEY_STAGING!,
  baseUrl: 'https://api.apollo.io/v1',
  rateLimit: { maxPerHour: 150, concurrency: 5 },
  features: { enrichment: true, sequences: true, webhooks: true },
  logging: { level: 'info', redactPII: true },
};

// config/production.ts
export const productionConfig: ApolloEnvConfig = {
  environment: 'production',
  apiKey: process.env.APOLLO_API_KEY_PROD!,
  baseUrl: 'https://api.apollo.io/v1',
  rateLimit: { maxPerHour: 600, concurrency: 10 },
  features: { enrichment: true, sequences: true, webhooks: true },
  logging: { level: 'warn', redactPII: true },
};
```

### Step 3: Build an Environment-Aware Client Factory
```typescript
// src/config/client-factory.ts
import axios, { AxiosInstance } from 'axios';

export function createEnvClient(config: ApolloEnvConfig): AxiosInstance {
  const validated = ApolloEnvConfigSchema.parse(config);

  const client = axios.create({
    baseURL: validated.baseUrl,
    headers: { 'Content-Type': 'application/json' },
    params: { api_key: validated.apiKey },
    timeout: validated.environment === 'development' ? 30_000 : 15_000,
  });

  // Environment-specific logging
  if (validated.logging.level === 'debug') {
    client.interceptors.request.use((req) => {
      console.log(`[${validated.environment}] ${req.method?.toUpperCase()} ${req.url}`);
      return req;
    });
  }

  // Feature gate check
  client.interceptors.request.use((req) => {
    if (req.url?.includes('/emailer_campaigns') && !validated.features.sequences) {
      throw new Error(`Sequences disabled in ${validated.environment}`);
    }
    if (req.url?.includes('/webhooks') && !validated.features.webhooks) {
      throw new Error(`Webhooks disabled in ${validated.environment}`);
    }
    return req;
  });

  return client;
}

// Auto-select config by NODE_ENV
export function getClient(): AxiosInstance {
  const env = process.env.NODE_ENV ?? 'development';
  const configs: Record<string, ApolloEnvConfig> = {
    development: developmentConfig,
    staging: stagingConfig,
    production: productionConfig,
  };
  return createEnvClient(configs[env] ?? configs.development);
}
```

### Step 4: Kubernetes Secret Management
```yaml
# k8s/apollo-secret-dev.yaml
apiVersion: v1
kind: Secret
metadata:
  name: apollo-credentials
  namespace: sales-tools-dev
type: Opaque
stringData:
  APOLLO_API_KEY: "dev-key-here"
  APOLLO_WEBHOOK_SECRET: "dev-webhook-secret"
---
# k8s/apollo-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollo-config
  namespace: sales-tools-dev
data:
  NODE_ENV: "development"
  APOLLO_BASE_URL: "https://api.apollo.io/v1"
  APOLLO_RATE_LIMIT_MAX: "50"
  APOLLO_LOG_LEVEL: "debug"
```

```yaml
# k8s/deployment.yaml (excerpt)
spec:
  containers:
    - name: apollo-service
      envFrom:
        - secretRef:
            name: apollo-credentials
        - configMapRef:
            name: apollo-config
```

### Step 5: Environment Promotion Script
```typescript
// src/scripts/promote-env.ts
async function promoteToStaging() {
  console.log('Running pre-promotion checks...');

  // 1. Verify staging API key works
  const stagingClient = createEnvClient(stagingConfig);
  const { data } = await stagingClient.post('/people/search', {
    q_organization_domains: ['apollo.io'],
    per_page: 1,
  });
  console.log(`Staging API key valid (${data.pagination.total_entries} results)`);

  // 2. Run integration tests against staging
  const { execSync } = await import('child_process');
  execSync('NODE_ENV=staging npm test', { stdio: 'inherit' });
  console.log('Integration tests passed on staging');

  // 3. Verify feature flags match expectations
  console.log('Features enabled:', stagingConfig.features);
  console.log('Rate limit:', stagingConfig.rateLimit);
  console.log('Promotion to staging: READY');
}
```

## Output
- Zod-validated environment config schema with feature flags and rate limits
- Per-environment config files (development, staging, production)
- Environment-aware client factory with feature gating
- Kubernetes Secret and ConfigMap manifests
- Promotion script with pre-flight validation

## Error Handling
| Issue | Resolution |
|-------|------------|
| Wrong environment | Check `NODE_ENV` variable; client factory falls back to development |
| Missing API key | Zod validation throws immediately with clear error message |
| Feature disabled | Client interceptor blocks requests with descriptive error |
| Rate limit mismatch | Each env has its own `rateLimit` config matching Apollo plan |

## Examples

### Verify All Environments
```typescript
const envs = ['development', 'staging', 'production'] as const;
for (const env of envs) {
  process.env.NODE_ENV = env;
  try {
    const client = getClient();
    const { data } = await client.post('/people/search', {
      q_organization_domains: ['apollo.io'],
      per_page: 1,
    });
    console.log(`${env}: OK (${data.pagination.total_entries} results)`);
  } catch (err: any) {
    console.error(`${env}: FAIL — ${err.message}`);
  }
}
```

## Resources
- [12-Factor App Configuration](https://12factor.net/config)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Zod Schema Validation](https://zod.dev/)

## Next Steps
Proceed to `apollo-observability` for monitoring setup.
