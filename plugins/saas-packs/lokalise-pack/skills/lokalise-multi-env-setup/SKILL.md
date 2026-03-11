---
name: lokalise-multi-env-setup
description: |
  Configure Lokalise across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Lokalise configurations.
  Trigger with phrases like "lokalise environments", "lokalise staging",
  "lokalise dev prod", "lokalise environment setup", "lokalise config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Multi Env Setup

## Overview
Configure Lokalise across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate Lokalise API keys per environment
- Secret management solution (environment variables, Vault, or cloud secrets)
- CI/CD pipeline with environment-aware deployment
- Application with environment detection logic

## Instructions
1. **Environment Strategy**
2. **Instructions**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set environment variable in deployment |
| Secret not found | Wrong secret path | Verify secret manager configuration |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Config validation fail | Missing field | Add startup validation with Zod schema |

## Examples
### Quick Environment Check
```typescript
const config = getLokaliseConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "LOKALISE_API_TOKEN is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getLokaliseConfig());
```

## Resources
- [Lokalise API](https://developers.lokalise.com)
- [12-Factor Config](https://12factor.net/config)

## Next Steps
For deployment, see `lokalise-deploy-integration`.
