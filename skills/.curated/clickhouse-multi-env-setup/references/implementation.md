# ClickHouse Multi-Environment Setup — Implementation

Full code for the configuration module, client factory, secrets management,
schema application, and environment guards. This is the depth behind the lean
skeleton in `SKILL.md` — copy each block into the indicated path and adapt the
environment names to your project.

## Step 2: Configuration Module

A single typed config keyed by `NODE_ENV`. Non-dev environments require secrets
and enforce HTTPS at startup so misconfiguration fails fast instead of leaking
plaintext traffic to ClickHouse Cloud.

```typescript
// src/config/clickhouse.ts
interface ClickHouseEnvConfig {
  url: string;
  username: string;
  password: string;
  database: string;
  maxConnections: number;
  requestTimeout: number;
  compression: boolean;
}

const configs: Record<string, ClickHouseEnvConfig> = {
  development: {
    url: 'http://localhost:8123',
    username: 'default',
    password: process.env.CLICKHOUSE_PASSWORD ?? 'dev_password',
    database: 'app_dev',
    maxConnections: 5,
    requestTimeout: 60_000,    // Longer for debugging
    compression: false,         // Easier to debug raw
  },
  staging: {
    url: process.env.CLICKHOUSE_HOST ?? 'https://staging.clickhouse.cloud:8443',
    username: process.env.CLICKHOUSE_USER ?? 'app_staging',
    password: process.env.CLICKHOUSE_PASSWORD!,
    database: 'app_staging',
    maxConnections: 10,
    requestTimeout: 30_000,
    compression: true,
  },
  production: {
    url: process.env.CLICKHOUSE_HOST!,
    username: process.env.CLICKHOUSE_USER!,
    password: process.env.CLICKHOUSE_PASSWORD!,
    database: 'app_prod',
    maxConnections: 20,
    requestTimeout: 30_000,
    compression: true,
  },
};

export function getConfig(): ClickHouseEnvConfig {
  const env = process.env.NODE_ENV ?? 'development';
  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);

  // Validate required fields in non-dev environments
  if (env !== 'development') {
    if (!config.password) throw new Error(`CLICKHOUSE_PASSWORD not set for ${env}`);
    if (!config.url.startsWith('https://')) {
      throw new Error(`ClickHouse ${env} must use HTTPS`);
    }
  }

  return config;
}
```

## Step 3: Client Factory

A lazily-initialized singleton client so the connection pool is created once per
process. Pool size, timeout, and compression all come from the per-environment
config above.

```typescript
// src/clickhouse/client.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';
import { getConfig } from '../config/clickhouse';

let client: ClickHouseClient | null = null;

export function getClient(): ClickHouseClient {
  if (!client) {
    const config = getConfig();
    client = createClient({
      url: config.url,
      username: config.username,
      password: config.password,
      database: config.database,
      max_open_connections: config.maxConnections,
      request_timeout: config.requestTimeout,
      compression: {
        request: config.compression,
        response: config.compression,
      },
    });
  }
  return client;
}
```

## Step 4: Secrets Management

Never commit credentials. Development uses a git-ignored `.env.local`; every
other environment pulls from a secret manager. Pick one of AWS, GCP, or Vault
per your infrastructure.

```bash
# --- Development ---
# .env.local (git-ignored)
CLICKHOUSE_PASSWORD=dev_password

# --- Staging (GitHub Actions) ---
# Set via: gh secret set CLICKHOUSE_PASSWORD_STAGING
# Access in workflow:
#   env:
#     CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_STAGING }}

# --- Production (AWS Secrets Manager) ---
aws secretsmanager create-secret \
  --name clickhouse/production \
  --secret-string '{"host":"https://prod.clickhouse.cloud:8443","password":"..."}'

# Fetch at runtime:
aws secretsmanager get-secret-value \
  --secret-id clickhouse/production \
  --query SecretString --output text

# --- Production (GCP Secret Manager) ---
echo -n "https://prod.clickhouse.cloud:8443" | \
  gcloud secrets create ch-prod-host --data-file=-

gcloud secrets versions access latest --secret=ch-prod-host

# --- Production (HashiCorp Vault) ---
vault kv put secret/clickhouse/prod \
  host="https://prod.clickhouse.cloud:8443" \
  password="..."
vault kv get -field=password secret/clickhouse/prod
```

## Step 5: Schema Management Across Environments

Apply SQL files in sorted order so migrations are deterministic. In production a
single failure aborts the run; in dev/staging it logs and continues so you can
see all failures at once.

```typescript
// scripts/apply-schema.ts
import { getClient } from '../src/clickhouse/client';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

async function applySchema() {
  const client = getClient();
  const env = process.env.NODE_ENV ?? 'development';
  const schemaDir = join(__dirname, '../src/clickhouse/schemas');
  const files = readdirSync(schemaDir).filter((f) => f.endsWith('.sql')).sort();

  console.log(`Applying ${files.length} schema files to ${env}...`);

  for (const file of files) {
    const sql = readFileSync(join(schemaDir, file), 'utf-8');
    try {
      await client.command({ query: sql });
      console.log(`  [OK] ${file}`);
    } catch (err) {
      console.error(`  [FAIL] ${file}: ${(err as Error).message}`);
      if (env === 'production') throw err;  // Fail hard in prod
    }
  }
}

applySchema();
```

## Step 6: Environment Guards

Guardrails that make destructive operations impossible to run against the wrong
environment. `requireNonProduction` blocks TRUNCATE/reset in prod, and
`validateDatabaseName` catches a stray connection pointed at the wrong database.

```typescript
// Prevent dangerous operations in production
function requireNonProduction(operation: string): void {
  if (process.env.NODE_ENV === 'production') {
    throw new Error(`${operation} is blocked in production`);
  }
}

// TRUNCATE only in dev/staging
async function resetTestData() {
  requireNonProduction('resetTestData');
  const client = getClient();
  await client.command({ query: 'TRUNCATE TABLE events' });
}

// Prevent accidental cross-environment queries
function validateDatabaseName(database: string): void {
  const env = process.env.NODE_ENV ?? 'development';
  const expected = `app_${env === 'development' ? 'dev' : env}`;
  if (database !== expected) {
    throw new Error(`Database mismatch: expected ${expected}, got ${database}`);
  }
}
```
