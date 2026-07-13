# Clay Multi-Environment Setup - Implementation Details

## Configuration

### Environment-Specific Configuration

```typescript
// config/clay.ts
interface ClayEnvConfig {
  apiKey: string;
  baseUrl: string;
  webhookSecret: string;
  rateLimit: number;
  timeout: number;
  retries: number;
}

const configs: Record<string, ClayEnvConfig> = {
  development: {
    apiKey: process.env.CLAY_DEV_API_KEY!,
    baseUrl: 'https://api.clay.com/v1',
    webhookSecret: process.env.CLAY_DEV_WEBHOOK_SECRET!,
    rateLimit: 10,
    timeout: 30000,
    retries: 1,
  },
  staging: {
    apiKey: process.env.CLAY_STAGING_API_KEY!,
    baseUrl: 'https://api.clay.com/v1',
    webhookSecret: process.env.CLAY_STAGING_WEBHOOK_SECRET!,
    rateLimit: 50,
    timeout: 15000,
    retries: 2,
  },
  production: {
    apiKey: process.env.CLAY_PROD_API_KEY!,
    baseUrl: 'https://api.clay.com/v1',
    webhookSecret: process.env.CLAY_PROD_WEBHOOK_SECRET!,
    rateLimit: 100,
    timeout: 10000,
    retries: 3,
  },
};

export function getClayConfig(): ClayEnvConfig {
  const env = process.env.NODE_ENV ?? 'development';
  const config = configs[env];
  if (!config) throw new Error(`No Clay config for env: ${env}`);
  return config;
}
```

## Advanced Patterns

### Secrets Management per Environment

```yaml
# .env.development
CLAY_DEV_API_KEY=clay_dev_xxx
CLAY_DEV_WEBHOOK_SECRET=whsec_dev_xxx

# .env.staging (use a secrets manager in CI)
CLAY_STAGING_API_KEY=vault:secret/clay/staging/api_key
CLAY_STAGING_WEBHOOK_SECRET=vault:secret/clay/staging/webhook_secret

# .env.production (never committed; injected by secrets manager)
# CLAY_PROD_API_KEY=<from vault/aws-secrets/gcp-secret-manager>
```

```typescript
// For production, resolve secrets from a manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function resolveSecret(name: string): Promise<string> {
  if (process.env.NODE_ENV !== 'production') {
    return process.env[name] ?? '';
  }
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/${name}/versions/latest`,
  });
  return version.payload?.data?.toString() ?? '';
}
```

### Environment-Aware Webhook Routing

```typescript
function getWebhookUrl(): string {
  const env = process.env.NODE_ENV ?? 'development';
  const routes: Record<string, string> = {
    development: 'https://dev.example.com/api/clay/webhook',
    staging: 'https://staging.example.com/api/clay/webhook',
    production: 'https://app.example.com/api/clay/webhook',
  };
  return routes[env]!;
}
```

### Migration Between Environments

```typescript
async function promoteConfig(from: string, to: string) {
  console.log(`Promoting Clay config from ${from} to ${to}`);

  // 1. Validate source env config works
  const sourceConfig = configs[from];
  await validateClayConnection(sourceConfig);

  // 2. Snapshot current target config
  const targetConfig = configs[to];
  const backup = { ...targetConfig };

  // 3. Apply non-secret config (rate limits, timeouts)
  targetConfig.rateLimit = sourceConfig.rateLimit;
  targetConfig.timeout = sourceConfig.timeout;
  targetConfig.retries = sourceConfig.retries;

  // 4. Validate target still works (secrets stay per-env)
  await validateClayConnection(targetConfig);

  console.log(`Config promoted from ${from} to ${to}`);
  return { backup, applied: targetConfig };
}
```

## Troubleshooting

### Environment Mismatch Diagnosis

```bash
# Verify which API key is active
curl -s -H "Authorization: Bearer $CLAY_API_KEY" \
  https://api.clay.com/v1/me | jq '{org: .organization, plan: .plan}'

# Compare across environments
for env in DEV STAGING PROD; do
  key_var="CLAY_${env}_API_KEY"
  echo "=== $env ==="
  curl -s -H "Authorization: Bearer ${!key_var}" \
    https://api.clay.com/v1/me | jq '.organization'
done
```

### Webhook Secret Mismatch

```typescript
function debugWebhookSignature(req: Request) {
  const signature = req.headers['x-clay-signature'];
  const body = JSON.stringify(req.body);
  const expected = crypto
    .createHmac('sha256', process.env.CLAY_WEBHOOK_SECRET!)
    .update(body)
    .digest('hex');

  console.log({
    received: signature,
    computed: expected,
    match: signature === expected,
    secretLength: process.env.CLAY_WEBHOOK_SECRET?.length,
  });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
