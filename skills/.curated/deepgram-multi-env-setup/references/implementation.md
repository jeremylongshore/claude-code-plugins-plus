# Deepgram Multi-Environment Setup - Implementation Details

## Environment Configuration

```typescript
interface DeepgramConfig {
  apiKey: string;
  projectId: string;
  model: string;
  features: { diarization: boolean; smartFormat: boolean; punctuate: boolean };
  limits: { maxConcurrent: number; maxDurationMinutes: number };
  callbacks: { baseUrl: string };
}

const configs: Record<string, DeepgramConfig> = {
  development: {
    apiKey: process.env.DEEPGRAM_API_KEY_DEV!,
    projectId: process.env.DEEPGRAM_PROJECT_ID_DEV!,
    model: 'base',
    features: { diarization: false, smartFormat: true, punctuate: true },
    limits: { maxConcurrent: 5, maxDurationMinutes: 10 },
    callbacks: { baseUrl: 'http://localhost:3000' },
  },
  staging: {
    apiKey: process.env.DEEPGRAM_API_KEY_STAGING!,
    projectId: process.env.DEEPGRAM_PROJECT_ID_STAGING!,
    model: 'nova-2',
    features: { diarization: true, smartFormat: true, punctuate: true },
    limits: { maxConcurrent: 20, maxDurationMinutes: 60 },
    callbacks: { baseUrl: 'https://staging.example.com' },
  },
  production: {
    apiKey: process.env.DEEPGRAM_API_KEY_PRODUCTION!,
    projectId: process.env.DEEPGRAM_PROJECT_ID_PRODUCTION!,
    model: 'nova-2',
    features: { diarization: true, smartFormat: true, punctuate: true },
    limits: { maxConcurrent: 100, maxDurationMinutes: 180 },
    callbacks: { baseUrl: 'https://api.example.com' },
  },
};

export function getConfig(): DeepgramConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  if (!config.apiKey) throw new Error(`DEEPGRAM_API_KEY not set for ${env}`);
  return config;
}
```

## Environment-Aware Client Factory

```typescript
import { createClient, DeepgramClient } from '@deepgram/sdk';

let clients: Map<string, DeepgramClient> = new Map();

export function getDeepgramClient(): DeepgramClient {
  const config = getConfig();
  const env = process.env.NODE_ENV || 'development';
  if (!clients.has(env)) clients.set(env, createClient(config.apiKey));
  return clients.get(env)!;
}

export async function transcribe(audioUrl: string) {
  const client = getDeepgramClient();
  const config = getConfig();
  const { result, error } = await client.listen.prerecorded.transcribeUrl(
    { url: audioUrl },
    { model: config.model, smart_format: config.features.smartFormat, punctuate: config.features.punctuate, diarize: config.features.diarization }
  );
  if (error) throw error;
  return result;
}
```

## Docker Compose Multi-Environment

```yaml
version: '3.8'

x-common: &common
  build: .
  restart: unless-stopped

services:
  app-dev:
    <<: *common
    environment:
      - NODE_ENV=development
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY_DEV}
      - DEEPGRAM_PROJECT_ID=${DEEPGRAM_PROJECT_ID_DEV}
    ports: ["3000:3000"]
    profiles: [development]

  app-staging:
    <<: *common
    environment:
      - NODE_ENV=staging
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY_STAGING}
      - DEEPGRAM_PROJECT_ID=${DEEPGRAM_PROJECT_ID_STAGING}
    ports: ["3001:3000"]
    profiles: [staging]

  app-production:
    <<: *common
    environment:
      - NODE_ENV=production
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY_PRODUCTION}
      - DEEPGRAM_PROJECT_ID=${DEEPGRAM_PROJECT_ID_PRODUCTION}
    ports: ["3002:3000"]
    deploy: { replicas: 3 }
    profiles: [production]
```

## Kubernetes ConfigMaps and Secrets

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: deepgram-config
data:
  MODEL: "nova-2"
  SMART_FORMAT: "true"
  PUNCTUATE: "true"
---
# k8s/overlays/development/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
configMapGenerator:
  - name: deepgram-config
    behavior: merge
    literals: [NODE_ENV=development, MODEL=base, MAX_CONCURRENT=5]
secretGenerator:
  - name: deepgram-secrets
    literals: [API_KEY=${DEEPGRAM_API_KEY_DEV}]
---
# k8s/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
configMapGenerator:
  - name: deepgram-config
    behavior: merge
    literals: [NODE_ENV=production, MAX_CONCURRENT=100]
secretGenerator:
  - name: deepgram-secrets
    literals: [API_KEY=${DEEPGRAM_API_KEY_PRODUCTION}]
```

## Environment Validation Script

```typescript
async function validateEnvironment(name: string, apiKey: string, projectId: string) {
  const result = { environment: name, valid: false, apiKeyValid: false, projectAccess: false, features: [] as string[], errors: [] as string[] };
  if (!apiKey) { result.errors.push('API key not set'); return result; }

  try {
    const client = createClient(apiKey);
    const { result: projectsResult, error } = await client.manage.getProjects();
    if (error) { result.errors.push(`API key error: ${error.message}`); return result; }
    result.apiKeyValid = true;

    const project = projectsResult.projects.find(p => p.project_id === projectId);
    if (!project) result.errors.push(`Project ${projectId} not accessible`);
    else result.projectAccess = true;

    const { error: transcribeError } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' }, { model: 'nova-2' }
    );
    if (!transcribeError) result.features.push('transcription');
    result.valid = result.apiKeyValid && result.projectAccess;
  } catch (error) { result.errors.push(error instanceof Error ? error.message : 'Unknown'); }
  return result;
}
```

## Terraform Multi-Environment

```hcl
variable "environment" { type = string }
variable "deepgram_api_key" { type = string; sensitive = true }
variable "config" { type = object({ model = string; max_concurrent = number }) }

resource "aws_secretsmanager_secret" "deepgram_api_key" {
  name = "deepgram/${var.environment}/api-key"
}

resource "aws_secretsmanager_secret_version" "deepgram_api_key" {
  secret_id     = aws_secretsmanager_secret.deepgram_api_key.id
  secret_string = var.deepgram_api_key
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
