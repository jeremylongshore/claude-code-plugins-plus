---
name: juicebox-multi-env-setup
description: |
  Configure Juicebox multi-environment setup with dev/staging/prod configs,
  secret management, and environment guards.
  Use when setting up separate Juicebox API keys per environment, building
  an environment-aware client factory, or preventing production data leaks in dev.
  Trigger with phrases like "juicebox environments", "juicebox staging",
  "juicebox dev prod", "juicebox environment setup".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Multi-Environment Setup

## Overview

Juicebox integrations need isolated dev/staging/prod environments so non-production contexts never touch real candidate data. This skill configures per-environment API keys, secret management, a singleton client factory, Kubernetes ConfigMap overlays, and runtime guards that prevent cross-environment data leaks.

## Prerequisites

- Separate Juicebox API tokens per environment (dev sandbox, staging, production)
- Node.js 18+ with TypeScript
- Secret management solution (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault)
- Kubernetes cluster with Kustomize (for ConfigMap overlays)
- `NODE_ENV` set correctly in each environment

## Instructions

### Step 1: Define environment-specific configuration

Each environment gets its own API key, base URL, timeout, and retry settings. Dev uses the Juicebox sandbox; staging and prod use the live API with different keys.

```typescript
// config/juicebox-env.ts
export interface JuiceboxEnvConfig {
  apiKeyEnvVar: string;
  baseUrl: string;
  timeout: number;
  retries: number;
  sandbox: boolean;
  maxResultsPerSearch: number;
}

const envConfigs: Record<string, JuiceboxEnvConfig> = {
  development: {
    apiKeyEnvVar: 'JUICEBOX_API_KEY_DEV',
    baseUrl: 'https://api.juicebox.ai',  // sandbox mode via token
    timeout: 30_000,
    retries: 1,
    sandbox: true,
    maxResultsPerSearch: 10
  },
  staging: {
    apiKeyEnvVar: 'JUICEBOX_API_KEY_STAGING',
    baseUrl: 'https://api.juicebox.ai',
    timeout: 30_000,
    retries: 2,
    sandbox: false,
    maxResultsPerSearch: 25
  },
  production: {
    apiKeyEnvVar: 'JUICEBOX_API_KEY_PROD',
    baseUrl: 'https://api.juicebox.ai',
    timeout: 60_000,
    retries: 3,
    sandbox: false,
    maxResultsPerSearch: 100
  }
};

export function getEnvConfig(): JuiceboxEnvConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = envConfigs[env];

  if (!config) {
    throw new Error(
      `Unknown NODE_ENV "${env}". Valid: ${Object.keys(envConfigs).join(', ')}`
    );
  }

  return config;
}
```

### Step 2: Wire secret management per environment

Dev allows plain env vars for convenience. Staging and production must pull credentials from a secret manager to avoid secrets in CI logs or container images.

```typescript
// lib/juicebox-secrets.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const secretPaths: Record<string, string> = {
  development: '',  // uses env var directly
  staging: 'projects/myproject/secrets/juicebox-staging-token/versions/latest',
  production: 'projects/myproject/secrets/juicebox-prod-token/versions/latest'
};

export async function getJuiceboxCredentials(): Promise<{
  username: string;
  apiToken: string;
}> {
  const env = process.env.NODE_ENV || 'development';

  if (env === 'development') {
    const username = process.env.JUICEBOX_USERNAME;
    const apiToken = process.env.JUICEBOX_API_TOKEN_DEV;
    if (!username || !apiToken) {
      throw new Error(
        'Set JUICEBOX_USERNAME and JUICEBOX_API_TOKEN_DEV for local development'
      );
    }
    return { username, apiToken };
  }

  // Staging/production: pull from GCP Secret Manager
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: secretPaths[env]
  });
  const payload = version.payload?.data?.toString();
  if (!payload) {
    throw new Error(`Empty secret for environment "${env}"`);
  }

  const parsed = JSON.parse(payload);
  return { username: parsed.username, apiToken: parsed.api_token };
}
```

### Step 3: Build an environment-aware client factory

A singleton factory that resolves config + credentials and returns a configured HTTP client. Lazy-initializes on first call.

```typescript
// lib/juicebox-client-factory.ts
import { getEnvConfig, JuiceboxEnvConfig } from '../config/juicebox-env';
import { getJuiceboxCredentials } from './juicebox-secrets';

interface JuiceboxClient {
  search(query: string, limit?: number): Promise<SearchResult>;
  enrich(profileId: string): Promise<EnrichedProfile>;
  config: JuiceboxEnvConfig;
}

let instance: JuiceboxClient | null = null;

export async function getJuiceboxClient(): Promise<JuiceboxClient> {
  if (instance) return instance;

  const config = getEnvConfig();
  const creds = await getJuiceboxCredentials();
  const authHeader = `token ${creds.username}:${creds.apiToken}`;

  async function apiCall(path: string, body: unknown): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), config.timeout);

    let lastError: Error | null = null;
    for (let attempt = 0; attempt <= config.retries; attempt++) {
      try {
        const resp = await fetch(`${config.baseUrl}${path}`, {
          method: 'POST',
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body),
          signal: controller.signal
        });

        if (!resp.ok) {
          throw new Error(`Juicebox API ${resp.status}: ${await resp.text()}`);
        }

        return resp.json();
      } catch (err) {
        lastError = err as Error;
        if (attempt < config.retries) {
          await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
        }
      } finally {
        clearTimeout(timeout);
      }
    }
    throw lastError;
  }

  instance = {
    config,
    async search(query: string, limit?: number) {
      const effectiveLimit = Math.min(
        limit ?? config.maxResultsPerSearch,
        config.maxResultsPerSearch
      );
      return apiCall('/api/search', { query, limit: effectiveLimit }) as Promise<SearchResult>;
    },
    async enrich(profileId: string) {
      return apiCall('/api/enrich', { profile_id: profileId }) as Promise<EnrichedProfile>;
    }
  };

  console.log(JSON.stringify({
    event: 'juicebox_client_initialized',
    env: process.env.NODE_ENV,
    baseUrl: config.baseUrl,
    sandbox: config.sandbox,
    timeout: config.timeout
  }));

  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Step 4: Create Kubernetes ConfigMaps per environment

Use Kustomize overlays so each environment gets the right non-secret config injected at deploy time.

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: juicebox-config
data:
  NODE_ENV: "production"
  JUICEBOX_TIMEOUT: "60000"
  JUICEBOX_RETRIES: "3"
  JUICEBOX_MAX_RESULTS: "100"
```

```yaml
# k8s/overlays/development/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: juicebox-config
data:
  NODE_ENV: "development"
  JUICEBOX_TIMEOUT: "30000"
  JUICEBOX_RETRIES: "1"
  JUICEBOX_MAX_RESULTS: "10"
  JUICEBOX_SANDBOX: "true"
```

```yaml
# k8s/overlays/staging/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: juicebox-config
data:
  NODE_ENV: "staging"
  JUICEBOX_TIMEOUT: "30000"
  JUICEBOX_RETRIES: "2"
  JUICEBOX_MAX_RESULTS: "25"
  JUICEBOX_SANDBOX: "false"
```

```yaml
# k8s/overlays/development/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patchesStrategicMerge:
  - configmap-patch.yaml
```

Apply per environment:

```bash
# Development
kubectl apply -k k8s/overlays/development/

# Staging
kubectl apply -k k8s/overlays/staging/

# Production (uses base directly)
kubectl apply -k k8s/base/
```

### Step 5: Add environment guards to prevent cross-environment data leaks

Runtime checks that block dangerous operations in the wrong environment. Dev cannot run bulk exports. Production cannot run data wipes.

```typescript
// lib/env-guards.ts
export class EnvironmentGuard {
  private readonly env: string;

  constructor() {
    this.env = process.env.NODE_ENV || 'development';
  }

  requireProduction(operation: string): void {
    if (this.env !== 'production') {
      throw new EnvironmentGuardError(
        `"${operation}" is only allowed in production (current: ${this.env})`
      );
    }
  }

  preventProduction(operation: string): void {
    if (this.env === 'production') {
      throw new EnvironmentGuardError(
        `"${operation}" is blocked in production`
      );
    }
  }

  requireNonProduction(operation: string): void {
    if (this.env === 'production') {
      throw new EnvironmentGuardError(
        `"${operation}" cannot run in production (current: ${this.env})`
      );
    }
  }

  isSandbox(): boolean {
    return this.env === 'development';
  }
}

export class EnvironmentGuardError extends Error {
  readonly statusCode = 403;
  constructor(message: string) {
    super(message);
    this.name = 'EnvironmentGuardError';
  }
}

// Usage
const guard = new EnvironmentGuard();

async function bulkExportCandidates(): Promise<void> {
  guard.requireProduction('bulk_export');
  // ... export logic that should never run in dev/staging
}

async function resetTestData(db: PrismaClient): Promise<void> {
  guard.preventProduction('reset_test_data');
  await db.profiles.deleteMany({});
  await db.searchHistory.deleteMany({});
}

async function seedSampleCandidates(db: PrismaClient): Promise<void> {
  guard.requireNonProduction('seed_sample_data');
  await db.profiles.createMany({
    data: [
      { name: 'Test User 1', email: 'test1@example.com', title: 'Engineer' },
      { name: 'Test User 2', email: 'test2@example.com', title: 'Designer' }
    ]
  });
}
```

## Output

- `config/juicebox-env.ts` — per-environment config (base URL, timeout, retries, sandbox flag, result limits)
- `lib/juicebox-secrets.ts` — credential resolver: env vars in dev, GCP Secret Manager in staging/prod
- `lib/juicebox-client-factory.ts` — singleton client factory with retry, timeout, and environment-aware defaults
- `k8s/base/configmap.yaml` + `k8s/overlays/*/` — Kustomize ConfigMaps per environment
- `lib/env-guards.ts` — runtime guards blocking production-only and dev-only operations

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `Unknown NODE_ENV "test"` | `NODE_ENV` set to a value not in config map | Add a config entry for `test` or alias it to `development` |
| `Empty secret for environment "production"` | Secret Manager returned empty payload | Verify secret version exists: `gcloud secrets versions list juicebox-prod-token` |
| `JUICEBOX_USERNAME not set` | Missing env vars in local dev | Add to `.env.local`: `JUICEBOX_USERNAME=your_user` and `JUICEBOX_API_TOKEN_DEV=your_token` |
| `EnvironmentGuardError: blocked in production` | Code tried to run a dev-only operation in prod | This is working as designed; move the operation to a dev/staging context |
| `Juicebox API 401` after deploy | ConfigMap has correct env but wrong secret mounted | Verify the Kubernetes Secret name matches the SecretManager path for that overlay |
| `AbortError: signal is aborted` | Request exceeded the environment's timeout setting | Increase `timeout` in the environment config, or optimize the search query (fewer results, simpler filters) |

## Examples

**Initialize the client in different environments:**

```typescript
import { getJuiceboxClient } from './lib/juicebox-client-factory';

// In development (NODE_ENV=development):
const client = await getJuiceboxClient();
console.log(client.config.sandbox);  // true
console.log(client.config.timeout);  // 30000
console.log(client.config.maxResultsPerSearch);  // 10

// In production (NODE_ENV=production):
const prodClient = await getJuiceboxClient();
console.log(prodClient.config.sandbox);  // false
console.log(prodClient.config.timeout);  // 60000
console.log(prodClient.config.maxResultsPerSearch);  // 100
```

**Use environment guards to protect destructive operations:**

```typescript
import { EnvironmentGuard } from './lib/env-guards';

const guard = new EnvironmentGuard();

// In development — this succeeds:
guard.preventProduction('wipe_test_data');
await db.profiles.deleteMany({});

// In production — this throws EnvironmentGuardError:
// guard.preventProduction('wipe_test_data');
// Error: "wipe_test_data" is blocked in production
```

**Deploy with environment-specific ConfigMaps:**

```bash
# Verify which config will be applied
kubectl kustomize k8s/overlays/staging/
# apiVersion: v1
# kind: ConfigMap
# metadata:
#   name: juicebox-config
# data:
#   NODE_ENV: "staging"
#   JUICEBOX_TIMEOUT: "30000"
#   JUICEBOX_RETRIES: "2"
#   JUICEBOX_MAX_RESULTS: "25"
#   JUICEBOX_SANDBOX: "false"

kubectl apply -k k8s/overlays/staging/
```

## Resources

- [Juicebox API docs](https://juicebox.ai/docs)
- [12-Factor App — Config](https://12factor.net/config)
- [GCP Secret Manager quickstart](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets)
- [Kustomize overlays](https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/)

## Next Steps

After environment setup, see `juicebox-observability` for monitoring each environment's API usage and health.
