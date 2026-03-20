---
name: evernote-multi-env-setup
description: |
  Configure multi-environment setup for Evernote integrations.
  Use when setting up dev, staging, and production environments,
  or managing environment-specific configurations.
  Trigger with phrases like "evernote environments", "evernote staging",
  "evernote dev setup", "multiple environments evernote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Multi-Environment Setup

## Overview
Configure separate development, staging, and production environments for Evernote integrations with proper isolation, configuration management, and environment-aware client factories.

## Prerequisites
- Multiple Evernote API keys (sandbox for dev/staging, production for prod)
- Environment management infrastructure
- CI/CD pipeline (see `evernote-ci-integration`)

## Instructions

### Step 1: Environment Configuration Files

Create per-environment config files that define the Evernote endpoint, sandbox flag, rate limit settings, and logging level.

```javascript
// config/environments.js
const configs = {
  development: {
    sandbox: true,
    apiUrl: 'https://sandbox.evernote.com',
    rateLimitDelayMs: 0,  // No throttle in dev
    logLevel: 'debug'
  },
  staging: {
    sandbox: true,
    apiUrl: 'https://sandbox.evernote.com',
    rateLimitDelayMs: 100,
    logLevel: 'info'
  },
  production: {
    sandbox: false,
    apiUrl: 'https://www.evernote.com',
    rateLimitDelayMs: 200,
    logLevel: 'warn'
  }
};

module.exports = configs[process.env.NODE_ENV || 'development'];
```

### Step 2: Environment Variables

Define environment-specific `.env` files. Each environment uses its own API key and token. The `EVERNOTE_SANDBOX` flag controls which Evernote endpoint the SDK connects to.

```bash
# .env.development - sandbox with dev token
EVERNOTE_SANDBOX=true
EVERNOTE_DEV_TOKEN=S=s1:U=...

# .env.production - production with OAuth
EVERNOTE_SANDBOX=false
EVERNOTE_CONSUMER_KEY=prod-key
EVERNOTE_CONSUMER_SECRET=prod-secret
```

### Step 3: Environment-Aware Client Factory

Build a factory that creates properly configured Evernote clients based on the active environment. Include validation that production never uses sandbox tokens.

### Step 4: Docker Compose for Local Development

Define services for the app, Redis (caching), and a webhook receiver (ngrok or localtunnel) in `docker-compose.yml`. Mount `.env.development` as environment file.

### Step 5: Health Check Endpoint

Create a `/health` endpoint that verifies Evernote API connectivity, reports the active environment, and checks cache availability.

```javascript
app.get('/health', async (req, res) => {
  const checks = {
    environment: process.env.NODE_ENV,
    sandbox: config.sandbox,
    evernoteApi: 'unknown',
    cacheConnected: false
  };
  try {
    await userStore.getUser();
    checks.evernoteApi = 'connected';
  } catch { checks.evernoteApi = 'error'; }
  res.json(checks);
});
```

For the full configuration loader, client factory, Docker setup, and CI/CD environment matrix, see [Implementation Guide](references/implementation-guide.md).

## Output
- Per-environment configuration files (development, staging, production)
- Environment-aware Evernote client factory
- `.env` templates for each environment
- Docker Compose setup for local development
- Health check endpoint with environment reporting
- CI/CD configuration with environment-specific secrets

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid consumer key` | Using sandbox key in production | Verify `EVERNOTE_SANDBOX` matches key type |
| Wrong environment | `NODE_ENV` not set | Default to `development`, warn in logs |
| Sandbox data in production | Environment misconfiguration | Add startup validation that checks key/env match |
| Docker connection refused | Service not started | Run `docker compose up` before testing |

## Resources
- [12 Factor App - Config](https://12factor.net/config)
- [Evernote Sandbox](https://sandbox.evernote.com)
- [Docker Compose](https://docs.docker.com/compose/)

## Next Steps
For observability setup, see `evernote-observability`.

## Examples

**Three-environment setup**: Development uses sandbox Developer Token for instant testing. Staging uses sandbox OAuth for integration testing. Production uses production OAuth with full rate limiting and monitoring.

**Docker local dev**: Run `docker compose up` to start the app with Redis caching and ngrok for webhook testing, all preconfigured for the sandbox environment.
