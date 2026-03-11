# OpenEvidence Multi-Environment Setup - Implementation Details

## Environment Configuration Files
```typescript
// config/environments/development.ts
export const developmentConfig = {
  env: 'development',
  openevidence: { baseUrl: 'https://api.sandbox.openevidence.com', timeout: 60000, retries: 1 },
  cache: { enabled: false, ttlSeconds: 0 },
  logging: { level: 'debug', prettyPrint: true },
  features: { deepConsult: true, webhooks: false, auditLogging: false },
};

// config/environments/production.ts
export const productionConfig = {
  env: 'production',
  openevidence: { baseUrl: 'https://api.openevidence.com', timeout: 30000, retries: 3, rateLimit: { enabled: true, requestsPerMinute: 300 } },
  cache: { enabled: true, ttlSeconds: 3600 },
  logging: { level: 'warn', prettyPrint: false },
  features: { deepConsult: true, webhooks: true, auditLogging: true },
};
```

## Configuration Loader
```typescript
export function loadConfig(env?: Environment) {
  const environment = env || (process.env.NODE_ENV as Environment) || 'development';
  const baseConfig = configs[environment];
  return {
    ...baseConfig,
    openevidence: {
      ...baseConfig.openevidence,
      apiKey: process.env.OPENEVIDENCE_API_KEY,
      orgId: process.env.OPENEVIDENCE_ORG_ID,
    },
  };
}
```

## Environment-Aware Client Factory
```typescript
export class OpenEvidenceClientFactory {
  private static instances: Map<string, OpenEvidenceClient> = new Map();
  static getClient(environment?: string): OpenEvidenceClient {
    const config = getConfig();
    const env = environment || config.env;
    if (!this.instances.has(env)) {
      this.instances.set(env, new OpenEvidenceClient({ apiKey: config.openevidence.apiKey, orgId: config.openevidence.orgId, baseUrl: config.openevidence.baseUrl }));
    }
    return this.instances.get(env)!;
  }
}
```

## Secret Management Per Environment
```typescript
const SECRET_PATHS: Record<string, SecretPaths> = {
  development: { apiKey: 'local', orgId: 'local' },
  staging: { apiKey: 'projects/staging-project/secrets/openevidence-api-key/versions/latest', orgId: '...' },
  production: { apiKey: 'projects/prod-project/secrets/openevidence-api-key/versions/latest', orgId: '...' },
};
```

## Environment Promotion Workflow
See the GitHub Actions workflow for gradual traffic shifting (10% -> 50% -> 100%) with smoke tests between stages.

## Environment Health Checks
```typescript
export async function checkEnvironmentHealth(): Promise<EnvironmentHealth> {
  const checks = { openevidence: { status: 'unknown' }, cache: { status: 'unknown' }, database: { status: 'unknown' } };
  // Check OpenEvidence connectivity, cache, and database
  // Determine overall status based on individual check results
  return { environment: config.env, status, checks, version: process.env.npm_package_version, timestamp: new Date().toISOString() };
}
```
