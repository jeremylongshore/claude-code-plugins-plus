---
name: salesforce-multi-env-setup
description: |
  Configure Salesforce across Developer, Sandbox, and Production environments with proper org management.
  Use when setting up multi-environment deployments, configuring per-environment credentials,
  or implementing sandbox-to-production promotion flows.
  Trigger with phrases like "salesforce environments", "salesforce sandbox",
  "salesforce dev prod", "salesforce org management", "salesforce sandbox types".
allowed-tools: Read, Write, Edit, Bash(sf:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Multi-Environment Setup

## Overview
Configure Salesforce integrations across Developer, Sandbox, and Production orgs with environment-specific credentials, login URLs, and deployment promotion flows.

## Prerequisites
- Production Salesforce org (Enterprise+ for Full sandbox)
- Salesforce CLI authenticated to all environments
- Secret management solution (Vault, AWS/GCP Secrets Manager)

## Instructions

### Step 1: Salesforce Environment Types

| Environment | Org Type | Login URL | Purpose | Data |
|------------|---------|-----------|---------|------|
| Development | Developer Edition or Scratch Org | login.salesforce.com | Local dev | Sample data |
| QA | Developer Sandbox | test.salesforce.com | Testing | Subset of prod |
| Staging | Full Sandbox | test.salesforce.com | Pre-prod validation | Copy of prod |
| Production | Production Org | login.salesforce.com | Live traffic | Real data |

### Step 2: Sandbox Types

| Sandbox Type | Data | Metadata | Refresh Interval | Use Case |
|-------------|------|----------|-------------------|----------|
| Developer | None | Copy of prod | 1 day | Feature development |
| Developer Pro | None | Copy of prod | 1 day | Integration testing |
| Partial Copy | Sampled | Copy of prod | 5 days | QA with realistic data |
| Full | Full copy | Copy of prod | 29 days | Staging, UAT, load testing |

### Step 3: Environment Configuration

```typescript
// src/config/salesforce.ts
interface SalesforceEnvConfig {
  loginUrl: string;
  username: string;
  apiVersion: string;
  isSandbox: boolean;
}

const envConfigs: Record<string, SalesforceEnvConfig> = {
  development: {
    loginUrl: 'https://login.salesforce.com', // Or test.salesforce.com for sandbox
    username: process.env.SF_USERNAME_DEV!,
    apiVersion: '59.0',
    isSandbox: false, // true if using a sandbox for dev
  },
  staging: {
    loginUrl: 'https://test.salesforce.com', // ALL sandboxes use test.salesforce.com
    username: process.env.SF_USERNAME_STAGING!,
    apiVersion: '59.0',
    isSandbox: true,
  },
  production: {
    loginUrl: 'https://login.salesforce.com',
    username: process.env.SF_USERNAME_PROD!,
    apiVersion: '59.0',
    isSandbox: false,
  },
};

export function getSalesforceConfig(): SalesforceEnvConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = envConfigs[env];
  if (!config) throw new Error(`No Salesforce config for environment: ${env}`);
  return config;
}
```

### Step 4: Authenticate to Multiple Orgs

```bash
# Authenticate to each environment with aliases
sf org login web --alias sf-dev --instance-url https://login.salesforce.com
sf org login web --alias sf-staging --instance-url https://test.salesforce.com
sf org login web --alias sf-prod --instance-url https://login.salesforce.com

# For CI — use JWT (no browser needed)
sf org login jwt \
  --client-id $SF_CLIENT_ID \
  --jwt-key-file server.key \
  --username ci-user@mycompany.com.staging \
  --alias sf-staging \
  --instance-url https://test.salesforce.com

# List all authenticated orgs
sf org list --all

# Set default org
sf config set target-org sf-dev
```

### Step 5: Secret Management by Environment

```bash
# Local development — .env.local (git-ignored)
SF_LOGIN_URL=https://test.salesforce.com
SF_USERNAME=dev-user@mycompany.com.dev
SF_PASSWORD=devpassword
SF_SECURITY_TOKEN=devtoken

# CI/CD (GitHub Actions)
# Use environment-specific secrets:
# Settings > Environments > "staging" > Add secret SF_USERNAME
# Settings > Environments > "production" > Add secret SF_USERNAME (different value)

# Production (Vault / Secrets Manager)
# AWS:
aws secretsmanager get-secret-value --secret-id salesforce/production

# GCP:
gcloud secrets versions access latest --secret=sf-prod-credentials

# HashiCorp Vault:
vault kv get -field=password secret/salesforce/production
```

### Step 6: Deployment Promotion Flow

```bash
# 1. Develop in scratch org or developer sandbox
sf project deploy start --target-org sf-dev

# 2. Run Apex tests in dev
sf apex run test --target-org sf-dev --result-format human

# 3. Deploy to staging sandbox
sf project deploy start --target-org sf-staging --test-level RunLocalTests

# 4. Run integration tests against staging
SF_LOGIN_URL=https://test.salesforce.com npm run test:integration

# 5. Deploy to production (requires test coverage)
sf project deploy start --target-org sf-prod --test-level RunLocalTests --wait 30

# Rollback if needed
sf project deploy cancel --target-org sf-prod
```

### Step 7: Environment Guards

```typescript
// Prevent destructive operations in production
function guardProductionOperation(operation: string): void {
  const config = getSalesforceConfig();

  if (!config.isSandbox && process.env.NODE_ENV === 'production') {
    const blocked = ['deleteAllAccounts', 'truncateContacts', 'resetData'];
    if (blocked.includes(operation)) {
      throw new Error(`Operation '${operation}' blocked in production Salesforce org`);
    }
  }
}

// Prevent using production credentials in dev
function validateEnvironment(): void {
  const config = getSalesforceConfig();
  if (process.env.NODE_ENV === 'development' && !config.isSandbox) {
    console.warn('WARNING: Development mode connected to production org!');
  }
}
```

## Output
- Multi-environment Salesforce configuration
- Sandbox types selected for each environment
- Credentials stored in platform-appropriate secrets manager
- Deployment promotion flow from dev to production
- Environment guards preventing accidental destructive operations

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `INVALID_LOGIN` in sandbox | Wrong login URL | Use `test.salesforce.com` for ALL sandboxes |
| Sandbox username format | Missing `.sandbox` suffix | Username format: `user@company.com.sandboxname` |
| Config merge fails | Wrong NODE_ENV | Verify environment variable |
| Production guard triggered | Destructive operation | Use sandbox for testing |

## Resources
- [Sandbox Types](https://help.salesforce.com/s/articleView?id=sf.deploy_sandboxes_intro.htm)
- [Sandbox Limitations](https://help.salesforce.com/s/articleView?id=sf.data_sandbox_environments.htm)
- [Change Sets](https://help.salesforce.com/s/articleView?id=sf.changesets.htm)
- [SFDX CLI Org Commands](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_org_commands_unified.htm)

## Next Steps
For observability setup, see `salesforce-observability`.
