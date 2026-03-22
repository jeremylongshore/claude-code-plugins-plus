---
name: langchain-multi-env-setup
description: |
  Configure LangChain across dev/staging/production environments
  with isolated API keys, environment-specific settings, and secrets.
  Trigger: "langchain environments", "langchain staging",
  "langchain dev prod", "environment configuration", "langchain env setup".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, workflow]

---
# LangChain Multi-Environment Setup

## Overview

Configure LangChain across development, staging, and production with separate API keys, environment-specific model settings, LangSmith project isolation, and validated configuration.

## Environment Strategy

| Environment | API Key Source | Model | LangSmith Project | Cache |
|-------------|---------------|-------|-------------------|-------|
| Development | `.env.local` | gpt-4o-mini | `dev-{user}` | Off |
| Staging | CI secrets | gpt-4o-mini | `staging` | Redis |
| Production | Secret Manager | gpt-4o | `production` | Redis |

## Step 1: Configuration with Zod Validation

```typescript
// config/langchain.ts
import { z } from "zod";
import "dotenv/config";

const EnvironmentSchema = z.enum(["development", "staging", "production"]);

const ConfigSchema = z.object({
  environment: EnvironmentSchema,
  openaiApiKey: z.string().min(1, "OPENAI_API_KEY is required"),
  model: z.string().default("gpt-4o-mini"),
  temperature: z.number().min(0).max(2).default(0),
  maxRetries: z.number().default(3),
  timeout: z.number().default(30000),
  langsmith: z.object({
    enabled: z.boolean(),
    apiKey: z.string().optional(),
    project: z.string(),
  }),
  cache: z.object({
    enabled: z.boolean(),
    ttlSeconds: z.number().default(300),
  }),
});

export type LangChainConfig = z.infer<typeof ConfigSchema>;

function detectEnvironment(): z.infer<typeof EnvironmentSchema> {
  const env = process.env.NODE_ENV ?? "development";
  if (env === "production") return "production";
  if (env === "staging" || process.env.VERCEL_ENV === "preview") return "staging";
  return "development";
}

const ENV_CONFIGS: Record<string, Partial<z.infer<typeof ConfigSchema>>> = {
  development: {
    model: "gpt-4o-mini",
    temperature: 0,
    timeout: 60000,
    langsmith: { enabled: true, project: `dev-${process.env.USER ?? "local"}` },
    cache: { enabled: false, ttlSeconds: 60 },
  },
  staging: {
    model: "gpt-4o-mini",
    temperature: 0,
    langsmith: { enabled: true, project: "staging" },
    cache: { enabled: true, ttlSeconds: 300 },
  },
  production: {
    model: "gpt-4o",
    temperature: 0,
    maxRetries: 5,
    timeout: 60000,
    langsmith: { enabled: true, project: "production" },
    cache: { enabled: true, ttlSeconds: 600 },
  },
};

export function loadConfig(): LangChainConfig {
  const env = detectEnvironment();
  const envConfig = ENV_CONFIGS[env];

  const raw = {
    environment: env,
    openaiApiKey: process.env.OPENAI_API_KEY,
    ...envConfig,
    langsmith: {
      ...envConfig?.langsmith,
      apiKey: process.env.LANGSMITH_API_KEY,
      enabled: process.env.LANGSMITH_TRACING === "true",
    },
  };

  const config = ConfigSchema.parse(raw);
  console.log(`[config] Environment: ${config.environment}, Model: ${config.model}`);
  return config;
}
```

## Step 2: Environment Files

```bash
# .env.example (commit this)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
NODE_ENV=development

# .env.local (git-ignored, for local dev)
OPENAI_API_KEY=sk-dev-...
LANGSMITH_API_KEY=lsv2_pt_dev_...
LANGSMITH_TRACING=true
NODE_ENV=development
```

```bash
# .gitignore
.env
.env.local
.env.*.local
```

## Step 3: Secret Management

```bash
# GitHub Actions — use environments
# Settings > Environments > staging > Secrets
# OPENAI_API_KEY, LANGSMITH_API_KEY

# GCP Secret Manager
echo -n "sk-prod-..." | gcloud secrets create openai-api-key-prod --data-file=-
echo -n "lsv2_..." | gcloud secrets create langsmith-api-key-prod --data-file=-

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name langchain/production/openai-key \
  --secret-string "sk-prod-..."
```

## Step 4: CI/CD with Environment Isolation

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      NODE_ENV: staging
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
      LANGSMITH_TRACING: "true"
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm test
      - run: gcloud run deploy langchain-api-staging --source .

  deploy-production:
    environment: production
    needs: deploy-staging
    env:
      NODE_ENV: production
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
      LANGSMITH_TRACING: "true"
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm test
      - run: gcloud run deploy langchain-api --source .
```

## Step 5: Use Config in Application

```typescript
// src/index.ts
import { loadConfig } from "./config/langchain";
import { createModel } from "./infra/llm/factory";

const config = loadConfig();

// Model automatically configured for environment
const model = createModel({
  provider: "openai",
  model: config.model,
  temperature: config.temperature,
  maxRetries: config.maxRetries,
  timeout: config.timeout,
});

// LangSmith tracing via env vars (automatic)
if (config.langsmith.enabled) {
  process.env.LANGSMITH_TRACING = "true";
  process.env.LANGSMITH_API_KEY = config.langsmith.apiKey ?? "";
  process.env.LANGSMITH_PROJECT = config.langsmith.project;
}
```

## Startup Validation

```typescript
// Fail fast on missing config
try {
  const config = loadConfig();
  console.log(`[startup] Config validated: ${config.environment}`);
} catch (error) {
  console.error("[startup] Invalid configuration:", error);
  process.exit(1);
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong environment detected | `NODE_ENV` not set | Set in deployment config |
| Secret not found | Wrong secret path | Verify in cloud console |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Config validation fail | Missing env var | Check `.env.example` for required vars |

## Resources

- [LangSmith Environments](https://docs.smith.langchain.com)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For deployment, see `langchain-deploy-integration`.
