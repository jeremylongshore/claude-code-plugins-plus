# Apollo Multi-Environment Setup - Implementation Guide

> Full implementation details and code examples for the `apollo-multi-env-setup` skill.

# Apollo Multi-Environment Setup

## Overview
Configure Apollo.io for multiple environments (development, staging, production) with proper isolation, configuration management, and deployment strategies.

## Environment Strategy

| Environment | Purpose | API Key | Rate Limit | Data Access |
|-------------|---------|---------|------------|-------------|
| Development | Local dev | Dev/Sandbox | Low (10/min) | Test data only |
| Staging | Pre-prod testing | Staging key | Medium (50/min) | Limited prod |
| Production | Live system | Production key | Full (100/min) | Full access |

## Configuration Structure

```typescript
// src/config/apollo/environments.ts
import { z } from 'zod';

const EnvironmentConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseUrl: z.string().url().default('https://api.apollo.io/v1'),
  rateLimit: z.number().positive(),
  timeout: z.number().positive().default(30000),
  cacheEnabled: z.boolean().default(true),
  cacheTtl: z.number().positive().default(300),
  features: z.object({
    search: z.boolean().default(true),
    enrichment: z.boolean().default(true),
    sequences: z.boolean().default(false),
    webhooks: z.boolean().default(false),
  }),
  logging: z.object({
    level: z.enum(['debug', 'info', 'warn', 'error']),
    redactPII: z.boolean().default(true),
  }),
});

type EnvironmentConfig = z.infer<typeof EnvironmentConfigSchema>;

const configs: Record<string, EnvironmentConfig> = {
  development: {
    apiKey: process.env.APOLLO_API_KEY_DEV || '',
    baseUrl: 'https://api.apollo.io/v1',
    rateLimit: 10,
    timeout: 30000,
    cacheEnabled: true,
    cacheTtl: 60, // Short cache in dev
    features: {
      search: true,
      enrichment: true,
      sequences: false, // Disabled in dev
      webhooks: false,
    },
    logging: {
      level: 'debug',
      redactPII: false, // Show full data in dev
    },
  },

  staging: {
    apiKey: process.env.APOLLO_API_KEY_STAGING || '',
    baseUrl: 'https://api.apollo.io/v1',
    rateLimit: 50,
    timeout: 30000,
    cacheEnabled: true,
    cacheTtl: 300,
    features: {
      search: true,
      enrichment: true,
      sequences: true,
      webhooks: true,
    },
    logging: {
      level: 'info',
      redactPII: true,
    },
  },

  production: {
    apiKey: process.env.APOLLO_API_KEY || '',
    baseUrl: 'https://api.apollo.io/v1',
    rateLimit: 90, // Buffer below 100
    timeout: 30000,
    cacheEnabled: true,
    cacheTtl: 900, // 15 min in prod
    features: {
      search: true,
      enrichment: true,
      sequences: true,
      webhooks: true,
    },
    logging: {
      level: 'warn',
      redactPII: true,
    },
  },
};

export function getConfig(): EnvironmentConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = configs[env];

  if (!config) {
    throw new Error(`Unknown environment: ${env}`);
  }

  // Validate configuration
  const result = EnvironmentConfigSchema.safeParse(config);
  if (!result.success) {
    throw new Error(`Invalid Apollo config for ${env}: ${result.error.message}`);
  }

  return result.data;
}

export function validateEnvironment(): void {
  const config = getConfig();

  if (!config.apiKey) {
    throw new Error('Apollo API key is required');
  }

  console.log(`Apollo configured for ${process.env.NODE_ENV || 'development'}`);
  console.log(`  Rate limit: ${config.rateLimit}/min`);
  console.log(`  Features: ${Object.entries(config.features).filter(([,v]) => v).map(([k]) => k).join(', ')}`);
}
```

## Environment Files

```bash
# .env.development
NODE_ENV=development
APOLLO_API_KEY_DEV=your-dev-api-key
APOLLO_RATE_LIMIT=10
APOLLO_CACHE_TTL=60
APOLLO_LOG_LEVEL=debug

# .env.staging
NODE_ENV=staging
APOLLO_API_KEY_STAGING=your-staging-api-key
APOLLO_RATE_LIMIT=50
APOLLO_CACHE_TTL=300
APOLLO_LOG_LEVEL=info

# .env.production
NODE_ENV=production
APOLLO_API_KEY=your-prod-api-key
APOLLO_RATE_LIMIT=90
APOLLO_CACHE_TTL=900
APOLLO_LOG_LEVEL=warn
```

## Kubernetes ConfigMaps

```yaml
# k8s/configmaps/apollo-config-dev.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollo-config
  namespace: development
data:
  NODE_ENV: "development"
  APOLLO_RATE_LIMIT: "10"
  APOLLO_CACHE_TTL: "60"
  APOLLO_LOG_LEVEL: "debug"
  APOLLO_FEATURES_SEARCH: "true"
  APOLLO_FEATURES_ENRICHMENT: "true"
  APOLLO_FEATURES_SEQUENCES: "false"
  APOLLO_FEATURES_WEBHOOKS: "false"
---
# k8s/configmaps/apollo-config-staging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollo-config
  namespace: staging
data:
  NODE_ENV: "staging"
  APOLLO_RATE_LIMIT: "50"
  APOLLO_CACHE_TTL: "300"
  APOLLO_LOG_LEVEL: "info"
  APOLLO_FEATURES_SEARCH: "true"
  APOLLO_FEATURES_ENRICHMENT: "true"
  APOLLO_FEATURES_SEQUENCES: "true"
  APOLLO_FEATURES_WEBHOOKS: "true"
---
# k8s/configmaps/apollo-config-prod.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollo-config
  namespace: production
data:
  NODE_ENV: "production"
  APOLLO_RATE_LIMIT: "90"
  APOLLO_CACHE_TTL: "900"
  APOLLO_LOG_LEVEL: "warn"
  APOLLO_FEATURES_SEARCH: "true"
  APOLLO_FEATURES_ENRICHMENT: "true"
  APOLLO_FEATURES_SEQUENCES: "true"
  APOLLO_FEATURES_WEBHOOKS: "true"
```

## Secrets Management

```yaml
# k8s/secrets/apollo-secrets.yaml (use sealed-secrets in practice)
apiVersion: v1
kind: Secret
metadata:
  name: apollo-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  api-key: ${APOLLO_API_KEY}
  webhook-secret: ${APOLLO_WEBHOOK_SECRET}
```

```bash
# Using External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: apollo-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-manager
    kind: ClusterSecretStore
  target:
    name: apollo-secrets
  data:
    - secretKey: api-key
      remoteRef:
        key: apollo-api-key-${ENV}
    - secretKey: webhook-secret
      remoteRef:
        key: apollo-webhook-secret-${ENV}
```

## Environment-Aware Client

```typescript
// src/lib/apollo/env-client.ts
import { getConfig } from '../../config/apollo/environments';

class EnvironmentAwareApolloClient {
  private config = getConfig();

  async request<T>(options: RequestOptions): Promise<T> {
    // Check feature flag
    if (!this.isFeatureEnabled(options.feature)) {
      throw new Error(`Feature ${options.feature} is disabled in ${process.env.NODE_ENV}`);
    }

    // Apply environment-specific rate limiting
    await this.rateLimiter.acquire();

    // Make request with environment config
    const response = await axios({
      ...options,
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      params: {
        ...options.params,
        api_key: this.config.apiKey,
      },
    });

    // Log based on environment
    this.log('info', `Apollo ${options.method} ${options.url}`, {
      status: response.status,
      duration: response.headers['x-response-time'],
    });

    return response.data;
  }

  private isFeatureEnabled(feature: string): boolean {
    return this.config.features[feature as keyof typeof this.config.features] ?? true;
  }

  private log(level: string, message: string, meta?: object): void {
    if (this.shouldLog(level)) {
      const sanitized = this.config.logging.redactPII
        ? this.redactPII(meta)
        : meta;
      console[level as 'log'](`[Apollo] ${message}`, sanitized);
    }
  }

  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.config.logging.level);
  }
}
```

## Testing Across Environments

```typescript
// tests/integration/env-tests.ts
describe('Environment Configuration', () => {
  const originalEnv = process.env.NODE_ENV;

  afterEach(() => {
    process.env.NODE_ENV = originalEnv;
  });

  it('loads development config correctly', () => {
    process.env.NODE_ENV = 'development';
    const config = getConfig();
    expect(config.rateLimit).toBe(10);
    expect(config.features.sequences).toBe(false);
  });

  it('loads staging config correctly', () => {
    process.env.NODE_ENV = 'staging';
    const config = getConfig();
    expect(config.rateLimit).toBe(50);
    expect(config.features.sequences).toBe(true);
  });

  it('loads production config correctly', () => {
    process.env.NODE_ENV = 'production';
    const config = getConfig();
    expect(config.rateLimit).toBe(90);
    expect(config.logging.redactPII).toBe(true);
  });

  it('throws on missing API key', () => {
    process.env.NODE_ENV = 'production';
    delete process.env.APOLLO_API_KEY;
    expect(() => validateEnvironment()).toThrow();
  });
});
```

## Environment Promotion

```bash
#!/bin/bash
# scripts/promote-to-staging.sh

echo "Promoting to staging environment..."

# Verify staging key is configured
if [ -z "$APOLLO_API_KEY_STAGING" ]; then
  echo "Error: APOLLO_API_KEY_STAGING not set"
  exit 1
fi

# Run staging tests
NODE_ENV=staging npm run test:integration

# Deploy to staging
kubectl apply -f k8s/configmaps/apollo-config-staging.yaml
kubectl apply -f k8s/secrets/apollo-secrets-staging.yaml
kubectl rollout restart deployment/apollo-service -n staging

# Verify deployment
kubectl rollout status deployment/apollo-service -n staging
curl -sf https://staging.example.com/health/apollo || exit 1

echo "Successfully promoted to staging"
```

## Output
- Environment-specific configurations
- Kubernetes ConfigMaps and Secrets
- Environment-aware client
- Feature flags per environment
- Environment promotion scripts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Wrong environment | Check NODE_ENV variable |
| Missing API key | Verify secrets configuration |
| Feature disabled | Check environment config |
| Rate limit mismatch | Verify config values |

## Resources
- [12-Factor App Configuration](https://12factor.net/config)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [External Secrets Operator](https://external-secrets.io/)

## Next Steps
Proceed to `apollo-observability` for monitoring setup.
