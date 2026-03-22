---
name: canva-multi-env-setup
description: |
  Configure Canva Connect API across development, staging, and production environments.
  Use when setting up multi-environment deployments, managing OAuth credentials per environment,
  or implementing environment-specific Canva configurations.
  Trigger with phrases like "canva environments", "canva staging",
  "canva dev prod", "canva environment setup", "canva config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Multi-Environment Setup

## Overview

Configure Canva Connect API integrations across development, staging, and production. Each environment needs separate OAuth integrations registered in the Canva developer portal with distinct redirect URIs.

## Environment Strategy

| Environment | Canva Integration | Redirect URI | Data |
|-------------|------------------|--------------|------|
| Development | `my-app-dev` | `http://localhost:3000/auth/canva/callback` | Test account |
| Staging | `my-app-staging` | `https://staging.myapp.com/auth/canva/callback` | Staging account |
| Production | `my-app-prod` | `https://myapp.com/auth/canva/callback` | Real users |

**Important:** Register a separate Canva integration per environment. Each gets its own client ID and secret.

## Configuration

```typescript
// src/config/canva.ts
interface CanvaEnvConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  baseUrl: string;  // Always api.canva.com — Canva has no sandbox API
  scopes: string[];
  debug: boolean;
}

const configs: Record<string, CanvaEnvConfig> = {
  development: {
    clientId: process.env.CANVA_CLIENT_ID!,
    clientSecret: process.env.CANVA_CLIENT_SECRET!,
    redirectUri: 'http://localhost:3000/auth/canva/callback',
    baseUrl: 'https://api.canva.com/rest/v1', // No sandbox exists
    scopes: ['design:content:write', 'design:content:read', 'design:meta:read', 'asset:write', 'asset:read'],
    debug: true,
  },
  staging: {
    clientId: process.env.CANVA_CLIENT_ID!,
    clientSecret: process.env.CANVA_CLIENT_SECRET!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
    baseUrl: 'https://api.canva.com/rest/v1',
    scopes: ['design:content:write', 'design:content:read', 'design:meta:read', 'asset:write', 'asset:read'],
    debug: false,
  },
  production: {
    clientId: process.env.CANVA_CLIENT_ID!,
    clientSecret: process.env.CANVA_CLIENT_SECRET!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
    baseUrl: 'https://api.canva.com/rest/v1',
    scopes: ['design:content:write', 'design:content:read', 'design:meta:read'],
    debug: false,
  },
};

export function getCanvaConfig(): CanvaEnvConfig {
  const env = process.env.NODE_ENV || 'development';
  return configs[env] || configs.development;
}
```

## Secret Management

### Local Development

```bash
# .env.local (git-ignored)
CANVA_CLIENT_ID=OCA_dev_xxxxxxxx
CANVA_CLIENT_SECRET=dev_xxxxxxxx
```

### GitHub Actions / CI

```bash
# Per-environment secrets
gh secret set CANVA_CLIENT_ID --env staging --body "OCA_staging_xxx"
gh secret set CANVA_CLIENT_SECRET --env staging --body "staging_xxx"
gh secret set CANVA_CLIENT_ID --env production --body "OCA_prod_xxx"
gh secret set CANVA_CLIENT_SECRET --env production --body "prod_xxx"
```

### Production — Cloud Secret Managers

```bash
# GCP Secret Manager
gcloud secrets create canva-client-id-prod --data-file=-
gcloud secrets create canva-client-secret-prod --data-file=-

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name canva/production/client-id \
  --secret-string "OCA_prod_xxx"

# HashiCorp Vault
vault kv put secret/canva/production \
  client_id="OCA_prod_xxx" \
  client_secret="prod_xxx"
```

## Environment Isolation Guards

```typescript
// Prevent accidental cross-environment operations
function assertEnvironment(expected: string): void {
  const actual = process.env.NODE_ENV || 'development';
  if (actual !== expected) {
    throw new Error(`Expected ${expected} environment, got ${actual}`);
  }
}

// Guard destructive operations
async function deleteAllUserDesigns(userId: string, token: string) {
  assertEnvironment('development'); // Block in staging/production
  // ...
}
```

## Token Storage per Environment

```typescript
// Development: file-based for convenience
// Staging/Production: encrypted database

function getTokenStore(): TokenStore {
  const env = process.env.NODE_ENV || 'development';

  if (env === 'development') {
    return new FileTokenStore('.canva-tokens.json'); // git-ignored
  }

  return new DatabaseTokenStore({
    connectionString: process.env.DATABASE_URL!,
    encryptionKey: process.env.TOKEN_ENCRYPTION_KEY!,
  });
}
```

## Canva-Specific Considerations

1. **No sandbox API** — Canva has no separate sandbox environment. All environments hit `api.canva.com/rest/v1`. Use separate Canva accounts for dev/staging.
2. **Separate integrations** — Each environment should be a distinct integration in the Canva developer portal to avoid redirect URI conflicts.
3. **Scope differences** — Use broader scopes in dev for testing, minimal scopes in production.
4. **Token isolation** — Never share tokens across environments. Refresh tokens are single-use.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong redirect URI | Environment mismatch | Use per-environment integration |
| Missing secret | Not deployed to env | Add via secret manager |
| Token cross-contamination | Shared token store | Isolate by environment prefix |
| Production guard triggered | Wrong NODE_ENV | Set correct environment variable |

## Resources

- [Canva Creating Integrations](https://www.canva.dev/docs/connect/creating-integrations/)
- [Canva Authentication](https://www.canva.dev/docs/connect/authentication/)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `canva-observability`.
