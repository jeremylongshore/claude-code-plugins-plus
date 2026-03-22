---
name: deepgram-multi-env-setup
description: |
  Configure Deepgram multi-environment setup for dev, staging, and production.
  Use when setting up environment-specific configurations, managing multiple
  Deepgram projects, or implementing environment isolation.
  Trigger: "deepgram environments", "deepgram staging", "deepgram dev prod",
  "multi-environment deepgram", "deepgram config management".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, environments, configuration]

---
# Deepgram Multi-Environment Setup

## Overview
Configure isolated Deepgram environments for development, staging, and production. Each environment uses a separate Deepgram project, scoped API keys, environment-specific model selection, and validated configuration. Includes typed config, client factory, Docker Compose profiles, and Kubernetes overlays.

## Environment Strategy

| Setting | Development | Staging | Production |
|---------|------------|---------|------------|
| Model | `base` (fast, cheap) | `nova-3` | `nova-3` |
| Concurrency | 5 | 20 | 100 |
| Diarization | Off | On | On |
| PII Redaction | Off | On | On |
| Callback URL | localhost:3000 | staging.example.com | api.example.com |
| Key Rotation | Manual | Monthly | 90-day auto |

## Instructions

### Step 1: Typed Environment Configuration

```typescript
interface DeepgramEnvConfig {
  apiKey: string;
  projectId: string;
  model: 'base' | 'nova-2' | 'nova-3';
  maxConcurrency: number;
  features: {
    diarize: boolean;
    smart_format: boolean;
    redact: string[] | false;
    summarize: boolean;
  };
  callbackBaseUrl?: string;
  timeout: number;
}

function loadConfig(env: string): DeepgramEnvConfig {
  const configs: Record<string, DeepgramEnvConfig> = {
    development: {
      apiKey: process.env.DEEPGRAM_API_KEY_DEV!,
      projectId: process.env.DEEPGRAM_PROJECT_ID_DEV!,
      model: 'base',
      maxConcurrency: 5,
      features: {
        diarize: false,
        smart_format: true,
        redact: false,
        summarize: false,
      },
      callbackBaseUrl: 'http://localhost:3000',
      timeout: 60000,
    },
    staging: {
      apiKey: process.env.DEEPGRAM_API_KEY_STAGING!,
      projectId: process.env.DEEPGRAM_PROJECT_ID_STAGING!,
      model: 'nova-3',
      maxConcurrency: 20,
      features: {
        diarize: true,
        smart_format: true,
        redact: ['pci', 'ssn'],
        summarize: true,
      },
      callbackBaseUrl: 'https://staging.example.com',
      timeout: 30000,
    },
    production: {
      apiKey: process.env.DEEPGRAM_API_KEY_PRODUCTION!,
      projectId: process.env.DEEPGRAM_PROJECT_ID_PRODUCTION!,
      model: 'nova-3',
      maxConcurrency: 100,
      features: {
        diarize: true,
        smart_format: true,
        redact: ['pci', 'ssn'],
        summarize: true,
      },
      callbackBaseUrl: 'https://api.example.com',
      timeout: 30000,
    },
  };

  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}. Use: development, staging, production`);
  if (!config.apiKey) throw new Error(`DEEPGRAM_API_KEY_${env.toUpperCase()} not set`);
  return config;
}

const env = process.env.NODE_ENV ?? 'development';
const config = loadConfig(env);
```

### Step 2: Client Factory

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

class DeepgramClientFactory {
  private static clients = new Map<string, DeepgramClient>();

  static getClient(env?: string): DeepgramClient {
    const environment = env ?? process.env.NODE_ENV ?? 'development';

    if (!this.clients.has(environment)) {
      const config = loadConfig(environment);
      this.clients.set(environment, createClient(config.apiKey));
      console.log(`Deepgram client created for: ${environment} (model: ${config.model})`);
    }

    return this.clients.get(environment)!;
  }

  // Convenience: transcribe with environment defaults
  static async transcribe(url: string, overrides: Record<string, any> = {}) {
    const environment = process.env.NODE_ENV ?? 'development';
    const config = loadConfig(environment);
    const client = this.getClient(environment);

    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url },
      {
        model: config.model,
        smart_format: config.features.smart_format,
        diarize: config.features.diarize,
        redact: config.features.redact || undefined,
        summarize: config.features.summarize ? 'v2' : undefined,
        ...overrides,
      }
    );
    if (error) throw error;
    return result;
  }

  // Reset for key rotation
  static reset(env?: string) {
    if (env) {
      this.clients.delete(env);
    } else {
      this.clients.clear();
    }
  }
}
```

### Step 3: Environment Variables Template

```bash
# .env.development
DEEPGRAM_API_KEY_DEV=dev-key-here
DEEPGRAM_PROJECT_ID_DEV=dev-project-id

# .env.staging
DEEPGRAM_API_KEY_STAGING=staging-key-here
DEEPGRAM_PROJECT_ID_STAGING=staging-project-id

# .env.production (use secret manager, not file)
# DEEPGRAM_API_KEY_PRODUCTION=production-key-here
# DEEPGRAM_PROJECT_ID_PRODUCTION=production-project-id
```

### Step 4: Docker Compose Multi-Profile

```yaml
# docker-compose.yml
x-common: &common
  build: .
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
    interval: 30s
    timeout: 10s

services:
  app-dev:
    <<: *common
    profiles: ["development"]
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DEEPGRAM_API_KEY_DEV=${DEEPGRAM_API_KEY_DEV}
      - DEEPGRAM_PROJECT_ID_DEV=${DEEPGRAM_PROJECT_ID_DEV}

  app-staging:
    <<: *common
    profiles: ["staging"]
    ports:
      - "3001:3000"
    environment:
      - NODE_ENV=staging
      - DEEPGRAM_API_KEY_STAGING=${DEEPGRAM_API_KEY_STAGING}
      - DEEPGRAM_PROJECT_ID_STAGING=${DEEPGRAM_PROJECT_ID_STAGING}

  app-production:
    <<: *common
    profiles: ["production"]
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DEEPGRAM_API_KEY_PRODUCTION=${DEEPGRAM_API_KEY_PRODUCTION}
      - DEEPGRAM_PROJECT_ID_PRODUCTION=${DEEPGRAM_PROJECT_ID_PRODUCTION}
    deploy:
      resources:
        limits:
          memory: 512M
```

```bash
# Usage:
docker compose --profile development up
docker compose --profile staging up
docker compose --profile production up
```

### Step 5: Kubernetes Kustomize Overlays

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: deepgram-config
data:
  DEEPGRAM_MODEL: "nova-3"
  DEEPGRAM_SMART_FORMAT: "true"

---
# k8s/overlays/development/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
bases:
  - ../../base
patchesStrategicMerge:
  - configmap-patch.yaml
secretGenerator:
  - name: deepgram-secrets
    literals:
      - api-key=dev-key-here

---
# k8s/overlays/development/configmap-patch.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: deepgram-config
data:
  DEEPGRAM_MODEL: "base"
  DEEPGRAM_MAX_CONCURRENCY: "5"
```

### Step 6: Environment Validation

```typescript
async function validateEnvironments() {
  const envs = ['development', 'staging', 'production'];
  const results: Record<string, { valid: boolean; error?: string }> = {};

  for (const env of envs) {
    try {
      const config = loadConfig(env);
      const client = createClient(config.apiKey);

      // Test 1: Key validity
      const { error: authError } = await client.manage.getProjects();
      if (authError) throw new Error(`Auth failed: ${authError.message}`);

      // Test 2: Project access
      const { error: projError } = await client.manage.getProject(config.projectId);
      if (projError) throw new Error(`Project access failed: ${projError.message}`);

      // Test 3: Transcription works
      const { error: sttError } = await client.listen.prerecorded.transcribeUrl(
        { url: 'https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav' },
        { model: config.model, smart_format: true }
      );
      if (sttError) throw new Error(`STT failed: ${sttError.message}`);

      results[env] = { valid: true };
      console.log(`[PASS] ${env}`);
    } catch (err: any) {
      results[env] = { valid: false, error: err.message };
      console.log(`[FAIL] ${env}: ${err.message}`);
    }
  }

  const allValid = Object.values(results).every(r => r.valid);
  console.log(`\nValidation: ${allValid ? 'ALL PASS' : 'FAILURES DETECTED'}`);
  return results;
}
```

## Output
- Typed environment configuration (dev/staging/prod)
- Singleton client factory per environment
- Docker Compose multi-profile setup
- Kubernetes Kustomize overlays
- Environment validation script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `DEEPGRAM_API_KEY_DEV not set` | Missing env var | Set in `.env.development` |
| Wrong model in staging | Config mismatch | Check `loadConfig` mapping |
| Cross-env key used | Shared key | Create separate projects per environment |
| Validation fails for one env | Key expired | Rotate key for that environment |

## Resources
- [Deepgram Projects](https://developers.deepgram.com/docs/projects)
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [Kustomize](https://kustomize.io/)
