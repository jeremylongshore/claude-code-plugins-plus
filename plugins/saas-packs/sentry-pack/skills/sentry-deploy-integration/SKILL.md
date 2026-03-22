---
name: sentry-deploy-integration
description: |
  Track deployments and release health in Sentry.
  Use when configuring deployment tracking, release health,
  or connecting deployments to error data.
  Trigger with phrases like "sentry deploy tracking", "sentry release health",
  "track deployments sentry", "sentry deployment notification".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, deployment, release-health, tracking]

---
# Sentry Deploy Integration

## Prerequisites
- Sentry CLI installed and authenticated
- Release created for the deployed version
- Build pipeline with deploy step access
- `SENTRY_AUTH_TOKEN` with `project:releases` scope

## Instructions

### 1. Complete Release + Deploy Workflow

```bash
#!/bin/bash
# scripts/deploy-with-sentry.sh
set -euo pipefail

VERSION="${1:-$(git rev-parse --short HEAD)}"
ENVIRONMENT="${2:-production}"
STARTED=$(date +%s)

# Step 1: Create release
sentry-cli releases new "$VERSION"

# Step 2: Associate commits
sentry-cli releases set-commits "$VERSION" --auto

# Step 3: Upload source maps
sentry-cli sourcemaps upload \
  --release="$VERSION" \
  --url-prefix="~/static/js" \
  --validate \
  ./dist

# Step 4: Finalize release
sentry-cli releases finalize "$VERSION"

# Step 5: Deploy application
echo "Deploying version $VERSION to $ENVIRONMENT..."
# your-deploy-command-here

FINISHED=$(date +%s)

# Step 6: Record deployment in Sentry
sentry-cli releases deploys "$VERSION" new \
  --env "$ENVIRONMENT" \
  --started "$STARTED" \
  --finished "$FINISHED"

echo "Deployment recorded: $VERSION -> $ENVIRONMENT (${FINISHED-STARTED}s)"
```

### 2. Deploy via Sentry API

```bash
# Create a deploy using the REST API
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "production",
    "name": "v1.2.3 production deploy",
    "url": "https://github.com/org/repo/actions/runs/12345",
    "dateStarted": "2026-03-22T10:00:00Z",
    "dateFinished": "2026-03-22T10:05:00Z"
  }' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/releases/$VERSION/deploys/"
```

### 3. Release Health Monitoring

Release health tracks crash-free sessions and users. Enable in SDK:

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: process.env.SENTRY_RELEASE,
  environment: 'production',

  // Session tracking is enabled by default in v8
  // autoSessionTracking: true,
});
```

**Release health metrics:**
- **Crash-free sessions** — % of sessions without an unhandled error
- **Crash-free users** — % of users without an unhandled error
- **Adoption** — % of sessions on this release vs previous
- **Error count** — total errors in this release
- **Session count** — total sessions in this release

### 4. Compare Releases

```bash
# List releases with stats
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/releases/?project=$SENTRY_PROJECT&per_page=5" \
  | python3 -c "
import json, sys
releases = json.load(sys.stdin)
for r in releases:
    print(f\"{r['version']}: {r.get('newGroups', 0)} new issues, {len(r.get('deploys', []))} deploys\")
"
```

### 5. Multi-Environment Deploy Tracking

```bash
# Track deployments across environments
# Staging deploy
sentry-cli releases deploys "$VERSION" new --env staging

# After staging validation passes:
sentry-cli releases deploys "$VERSION" new --env production

# Sentry dashboard shows deployment timeline:
# staging (2:00 PM) -> production (4:30 PM)
```

### 6. Environment-Specific SDK Configuration

```typescript
// config/sentry.ts
const envConfig: Record<string, Partial<Sentry.NodeOptions>> = {
  production: {
    tracesSampleRate: 0.1,
    sampleRate: 1.0,
    debug: false,
  },
  staging: {
    tracesSampleRate: 0.5,
    sampleRate: 1.0,
    debug: false,
  },
  development: {
    tracesSampleRate: 1.0,
    sampleRate: 1.0,
    debug: true,
  },
};

const env = process.env.NODE_ENV || 'development';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: env,
  release: process.env.SENTRY_RELEASE,
  ...envConfig[env],
});
```

### 7. Rollback Tracking

```bash
# When rolling back, create a new deploy pointing to the old release
ROLLBACK_VERSION="v1.1.0"  # Previous stable version

sentry-cli releases deploys "$ROLLBACK_VERSION" new \
  --env production \
  --name "Rollback from $CURRENT_VERSION"

# Sentry shows the rollback in the release timeline
# and attributes new errors to the rolled-back version
```

### 8. Deploy Notification Webhooks

Configure in **Project Settings > Integrations** for deploy notifications:
- Slack: "Release v1.2.3 deployed to production"
- PagerDuty: Post-deploy error spike monitoring
- Custom webhook: `POST /webhook/sentry-deploy`

```typescript
// Custom webhook handler
app.post('/webhook/sentry-deploy', (req, res) => {
  const { action, data } = req.body;

  if (action === 'deploy') {
    console.log(`Deploy: ${data.release} -> ${data.environment}`);
    // Trigger post-deploy health checks
    runHealthChecks(data.release, data.environment);
  }

  res.status(200).send('ok');
});
```

## Output
- Deployments recorded with environment and timestamps
- Release health metrics tracking crash-free sessions
- Multi-environment deploy timeline visible in Sentry
- Rollback tracking recording version changes
- Deploy notifications sent to team channels

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `release not found` | Deploy created before release | Run `sentry-cli releases new $VERSION` first |
| No release health data | `autoSessionTracking` disabled | Ensure SDK v8 default is not overridden |
| Wrong environment in events | `environment` not set in SDK | Explicitly set `environment` in `Sentry.init()` |
| Deploy timestamps wrong | Missing `--started`/`--finished` flags | Capture timestamps before and after deploy step |
| Crash-free rate inaccurate | Mixed SDK versions across instances | Ensure all instances use the same release version |

## Resources
- [Release Setup](https://docs.sentry.io/product/releases/setup/)
- [Release Health](https://docs.sentry.io/product/releases/health/)
- [Deploy CLI](https://docs.sentry.io/cli/releases/#creating-deploys)
- [Release API](https://docs.sentry.io/api/releases/)
