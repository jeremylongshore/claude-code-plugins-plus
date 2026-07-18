# Notion Multi-Environment Setup — Full Implementation

Complete walkthrough for the three build steps. SKILL.md carries the lean version;
this file holds every code block and per-platform detail.

## Step 1: Create Per-Environment Integrations and Env-Aware Client

Create separate integrations at <https://www.notion.so/my-integrations> with scoped capabilities:

| Environment | Integration Name | Capabilities | Timeout | Log Level |
| ------------- | ----------------- | -------------- | --------- | ----------- |
| Development | `my-app-dev` | All (read+update+insert+delete) | 60s | DEBUG |
| Staging | `my-app-staging` | Read + Update + Insert | 30s | WARN |
| Production | `my-app-prod` | Minimum required only | 30s | ERROR |

**TypeScript — environment-aware client factory:**

```typescript
import { Client, LogLevel } from '@notionhq/client';

interface NotionEnvConfig {
  token: string;
  databaseIds: Record<string, string>;
  logLevel: LogLevel;
  timeoutMs: number;
  maxRetries: number;
}

const ENV_DEFAULTS: Record<string, Omit<NotionEnvConfig, 'token' | 'databaseIds'>> = {
  development: { logLevel: LogLevel.DEBUG, timeoutMs: 60_000, maxRetries: 0 },
  staging:     { logLevel: LogLevel.WARN,  timeoutMs: 30_000, maxRetries: 2 },
  production:  { logLevel: LogLevel.ERROR, timeoutMs: 30_000, maxRetries: 3 },
};

function getConfig(): NotionEnvConfig {
  const env = process.env.NODE_ENV || 'development';
  const defaults = ENV_DEFAULTS[env] ?? ENV_DEFAULTS.development;

  const token = process.env.NOTION_TOKEN;
  if (!token) {
    throw new Error(
      `NOTION_TOKEN not set for "${env}". ` +
      `Set it in .env.${env} or your secret manager.`
    );
  }

  return {
    token,
    databaseIds: {
      tasks: process.env.NOTION_TASKS_DB_ID!,
      users: process.env.NOTION_USERS_DB_ID!,
      logs:  process.env.NOTION_LOGS_DB_ID!,
    },
    ...defaults,
  };
}

export function createNotionClient(): Client {
  const config = getConfig();
  return new Client({
    auth: config.token,
    logLevel: config.logLevel,
    timeoutMs: config.timeoutMs,
  });
}

export function getDatabaseId(name: string): string {
  const config = getConfig();
  const id = config.databaseIds[name];
  if (!id) {
    throw new Error(
      `Database ID not configured for "${name}". ` +
      `Set NOTION_${name.toUpperCase()}_DB_ID in your environment.`
    );
  }
  return id;
}
```

**Python — environment-aware client factory:**

```python
import os
from notion_client import Client

ENV_CONFIGS = {
    "development": {"timeout_ms": 60_000, "log_level": "DEBUG"},
    "staging":     {"timeout_ms": 30_000, "log_level": "WARNING"},
    "production":  {"timeout_ms": 30_000, "log_level": "ERROR"},
}

def create_notion_client() -> Client:
    env = os.getenv("APP_ENV", "development")
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError(f"NOTION_TOKEN not set for '{env}'")

    cfg = ENV_CONFIGS.get(env, ENV_CONFIGS["development"])
    return Client(auth=token, timeout_ms=cfg["timeout_ms"])

def get_database_id(name: str) -> str:
    env_var = f"NOTION_{name.upper()}_DB_ID"
    db_id = os.getenv(env_var)
    if not db_id:
        raise ValueError(f"{env_var} not set")
    return db_id
```

## Step 2: Secret Management and Environment Files

**Local development — `.env` files (git-ignored):**

```bash
# .env.development
NOTION_TOKEN=ntn_dev_xxxxxxxxxxxxxxxxxxxxx
NOTION_TASKS_DB_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
NOTION_USERS_DB_ID=ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj
NOTION_LOGS_DB_ID=11111111-2222-3333-4444-555555555555

# .env.staging
NOTION_TOKEN=ntn_staging_xxxxxxxxxxxxxxxxx
NOTION_TASKS_DB_ID=66666666-7777-8888-9999-000000000000
NOTION_USERS_DB_ID=aaaaaaaa-1111-2222-3333-444444444444

# Production tokens NEVER stored as files — use secret manager
```

**AWS Secrets Manager:**

```bash
# Store production secrets
aws secretsmanager create-secret \
  --name "notion/production" \
  --secret-string '{
    "token": "ntn_prod_xxxxxxxxxxxxxxxxx",
    "tasks_db": "abcdefab-cdef-abcd-efab-cdefabcdefab",
    "users_db": "12345678-abcd-efgh-ijkl-123456789012"
  }'

# Retrieve in application
aws secretsmanager get-secret-value --secret-id notion/production --query SecretString --output text
```

**GCP Secret Manager:**

```bash
# Store each secret individually
echo -n "ntn_prod_xxxxxxxxxxxxxxxxx" | gcloud secrets create notion-token-prod --data-file=-
echo -n "abcdefab-cdef-abcd-efab-cdefabcdefab" | gcloud secrets create notion-tasks-db-prod --data-file=-

# Inject into Cloud Run service
gcloud run deploy my-service \
  --set-secrets=NOTION_TOKEN=notion-token-prod:latest,NOTION_TASKS_DB_ID=notion-tasks-db-prod:latest
```

**HashiCorp Vault:**

```bash
vault kv put secret/notion/production \
  token=ntn_prod_xxxxxxxxxxxxxxxxx \
  tasks_db_id=abcdefab-cdef-abcd-efab-cdefabcdefab
```

## Step 3: Environment Guards and CI/CD

**Environment guards — prevent cross-environment mistakes:**

```typescript
function requireEnvironment(required: 'development' | 'staging' | 'production') {
  const current = process.env.NODE_ENV || 'development';
  if (current !== required) {
    throw new Error(
      `This operation requires "${required}" but running in "${current}". Aborting.`
    );
  }
}

// Block destructive operations in production
function requireNonProduction() {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('Destructive operation blocked in production');
  }
}

// Usage
async function seedTestData(notion: Client, dbId: string) {
  requireNonProduction(); // Throws in production
  await notion.pages.create({
    parent: { database_id: dbId },
    properties: {
      Name: { title: [{ text: { content: 'Test Record' } }] },
      Status: { select: { name: 'Test' } },
    },
  });
}

async function runMigration(notion: Client) {
  requireEnvironment('production'); // Only runs in production
  // ... migration logic
}
```

**Startup validation — fail fast on missing config:**

```typescript
function validateNotionConfig() {
  const env = process.env.NODE_ENV || 'development';
  const required = ['NOTION_TOKEN', 'NOTION_TASKS_DB_ID'];
  const missing = required.filter(v => !process.env[v]);

  if (missing.length > 0) {
    throw new Error(
      `Missing env vars for "${env}": ${missing.join(', ')}. ` +
      `Check .env.${env} or your secret manager.`
    );
  }

  // Validate token prefix matches environment
  const token = process.env.NOTION_TOKEN!;
  if (env === 'production' && token.includes('dev')) {
    throw new Error('Production detected but NOTION_TOKEN contains "dev" — likely wrong token');
  }

  console.log(`Notion configured for ${env} (token: ${token.slice(0, 8)}...)`);
}
```

**CI/CD deployment with per-environment secrets:**

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    environment: staging
    env:
      NODE_ENV: staging
      NOTION_TOKEN: ${{ secrets.NOTION_TOKEN_STAGING }}
      NOTION_TASKS_DB_ID: ${{ secrets.NOTION_TASKS_DB_ID_STAGING }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run deploy:staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    env:
      NODE_ENV: production
      NOTION_TOKEN: ${{ secrets.NOTION_TOKEN_PROD }}
      NOTION_TASKS_DB_ID: ${{ secrets.NOTION_TASKS_DB_ID_PROD }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: INTEGRATION=true npm run test:integration
      - run: npm run deploy:production
```
