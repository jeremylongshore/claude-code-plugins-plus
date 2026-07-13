# Gamma Multi-Environment Setup - Implementation Details

## Environment Configuration Structure

```typescript
// config/gamma.config.ts
interface GammaConfig {
  apiKey: string;
  baseUrl: string;
  timeout: number;
  retries: number;
  debug: boolean;
}

type Environment = 'development' | 'staging' | 'production';

const configs: Record<Environment, Partial<GammaConfig>> = {
  development: {
    baseUrl: 'https://api.gamma.app/v1',
    timeout: 60000,
    retries: 1,
    debug: true,
  },
  staging: {
    baseUrl: 'https://api.gamma.app/v1',
    timeout: 45000,
    retries: 2,
    debug: true,
  },
  production: {
    baseUrl: 'https://api.gamma.app/v1',
    timeout: 30000,
    retries: 3,
    debug: false,
  },
};

export function getConfig(): GammaConfig {
  const env = (process.env.NODE_ENV || 'development') as Environment;
  const envConfig = configs[env];

  return {
    apiKey: process.env.GAMMA_API_KEY!,
    ...envConfig,
  } as GammaConfig;
}
```

## Environment-Specific API Keys

```bash
# .env.development
GAMMA_API_KEY=gamma_dev_xxx...
GAMMA_MOCK=false
NODE_ENV=development

# .env.staging
GAMMA_API_KEY=gamma_staging_xxx...
GAMMA_MOCK=false
NODE_ENV=staging

# .env.production
GAMMA_API_KEY=gamma_prod_xxx...
GAMMA_MOCK=false
NODE_ENV=production
```

## Secret Management Integration

```typescript
// lib/secrets.ts
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

const secretsManager = new SecretsManager({ region: 'us-east-1' });

interface SecretCache {
  value: string;
  expiresAt: number;
}

const cache: Map<string, SecretCache> = new Map();
const CACHE_TTL = 300000; // 5 minutes

export async function getSecret(name: string): Promise<string> {
  const cached = cache.get(name);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.value;
  }

  const env = process.env.NODE_ENV || 'development';
  const secretName = `gamma/${env}/${name}`;

  const response = await secretsManager.getSecretValue({
    SecretId: secretName,
  });

  const value = response.SecretString!;
  cache.set(name, { value, expiresAt: Date.now() + CACHE_TTL });

  return value;
}
```

## Client Factory

```typescript
// lib/gamma-factory.ts
import { GammaClient } from '@gamma/sdk';
import { getConfig } from '../config/gamma.config';
import { getSecret } from './secrets';

let clients: Map<string, GammaClient> = new Map();

export async function getGammaClient(): Promise<GammaClient> {
  const env = process.env.NODE_ENV || 'development';

  if (clients.has(env)) {
    return clients.get(env)!;
  }

  const config = getConfig();

  const apiKey = env === 'production'
    ? await getSecret('api-key')
    : config.apiKey;

  const client = new GammaClient({
    apiKey,
    baseUrl: config.baseUrl,
    timeout: config.timeout,
    retries: config.retries,
    debug: config.debug,
  });

  clients.set(env, client);
  return client;
}
```

## Environment Guards

```typescript
// lib/env-guards.ts
export function requireProduction(): void {
  if (process.env.NODE_ENV !== 'production') {
    throw new Error('This operation requires production environment');
  }
}

export function blockProduction(): void {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('This operation is blocked in production');
  }
}

async function deleteAllPresentations() {
  blockProduction();
  const gamma = await getGammaClient();
  const presentations = await gamma.presentations.list();
  for (const p of presentations) {
    await gamma.presentations.delete(p.id);
  }
}
```

## CI/CD Environment Configuration

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches:
      - develop    # → staging
      - main       # → production

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        env:
          GAMMA_API_KEY: ${{ secrets.GAMMA_API_KEY_STAGING }}
          NODE_ENV: staging
        run: |
          npm ci
          npm run build
          npm run deploy:staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Production
        env:
          GAMMA_API_KEY: ${{ secrets.GAMMA_API_KEY_PRODUCTION }}
          NODE_ENV: production
        run: |
          npm ci
          npm run build
          npm run deploy:production
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
