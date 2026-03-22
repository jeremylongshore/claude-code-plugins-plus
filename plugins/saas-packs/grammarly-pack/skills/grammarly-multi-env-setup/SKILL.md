---
name: grammarly-multi-env-setup
description: |
  Configure Grammarly across multiple environments.
  Use when setting up dev/staging/prod environments with Grammarly API.
  Trigger with phrases like "grammarly multi-env", "grammarly environments",
  "grammarly staging", "grammarly dev prod setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Multi-Environment Setup

## Instructions

### Step 1: Environment-Specific Credentials

```typescript
const config = {
  development: {
    clientId: process.env.GRAMMARLY_DEV_CLIENT_ID!,
    clientSecret: process.env.GRAMMARLY_DEV_CLIENT_SECRET!,
  },
  production: {
    clientId: process.env.GRAMMARLY_PROD_CLIENT_ID!,
    clientSecret: process.env.GRAMMARLY_PROD_CLIENT_SECRET!,
  },
};

const env = process.env.NODE_ENV || 'development';
const client = new GrammarlyClient(config[env].clientId, config[env].clientSecret);
```

### Step 2: Rate Limit Tiers by Environment

```typescript
const rateLimits = {
  development: { concurrency: 1, intervalCap: 2 },
  staging: { concurrency: 2, intervalCap: 5 },
  production: { concurrency: 5, intervalCap: 10 },
};
```

## Resources

- [Grammarly API](https://developer.grammarly.com/)
