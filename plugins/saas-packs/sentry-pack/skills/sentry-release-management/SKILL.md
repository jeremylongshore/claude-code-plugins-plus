---
name: sentry-release-management
description: |
  Manage Sentry releases, source maps, and commit tracking.
  Use when creating releases, tracking commits,
  or managing release artifacts.
  Trigger with phrases like "sentry release", "sentry commits",
  "manage sentry versions", "sentry release workflow".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Bash(npx:*), Bash(git:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, workflow, releases, source-maps]

---
# Sentry Release Management

## Prerequisites
- Sentry CLI installed: `npm install -g @sentry/cli`
- `SENTRY_AUTH_TOKEN` with `project:releases` scope
- `SENTRY_ORG` and `SENTRY_PROJECT` environment variables set
- Source maps generated during build (e.g., `tsc --sourceMap`)

## Instructions

### 1. Create a Release

```bash
# Use git SHA as release version (recommended)
VERSION=$(git rev-parse --short HEAD)

# Or use package.json version
VERSION=$(node -p "require('./package.json').version")

# Or combine: my-app@1.2.3+abc1234
VERSION="my-app@$(node -p "require('./package.json').version")+$(git rev-parse --short HEAD)"

# Create the release (stays "unreleased" until finalized)
sentry-cli releases new "$VERSION"
```

### 2. Associate Commits

```bash
# Auto-detect commits from git log (requires GitHub/GitLab integration)
sentry-cli releases set-commits "$VERSION" --auto

# Or specify commit range manually
sentry-cli releases set-commits "$VERSION" \
  --commit "my-org/my-repo@from_sha..to_sha"
```

Commit association enables:
- "Suspect Commits" showing which commits likely introduced an error
- "Suggested Assignees" based on commit authors
- Linking Sentry issues to PRs and commits

### 3. Upload Source Maps

```bash
# Upload all .js and .map files from dist/
sentry-cli sourcemaps upload \
  --release="$VERSION" \
  --url-prefix="~/static/js" \
  ./dist

# For multiple directories
sentry-cli sourcemaps upload \
  --release="$VERSION" \
  --url-prefix="~/" \
  ./dist/client ./dist/server

# Validate source maps before upload (catches errors early)
sentry-cli sourcemaps upload \
  --release="$VERSION" \
  --url-prefix="~/static/js" \
  --validate \
  ./dist
```

**URL prefix rules:**
- `~/` matches any scheme/host (recommended)
- `~/static/js` matches `https://example.com/static/js/bundle.js`
- Must match the URL where your JS files are served

### 4. Finalize the Release

```bash
# Finalize marks the release as deployed and sets the timestamp
sentry-cli releases finalize "$VERSION"
```

Finalizing affects:
- How issues are resolved ("next release" resolution)
- What release is used as the base for commit association
- Activity stream entry creation

### 5. Create a Deploy

```bash
# Notify Sentry which environment the release was deployed to
sentry-cli releases deploys "$VERSION" new \
  --env production \
  --started $(date +%s) \
  --finished $(date +%s)

# For staging
sentry-cli releases deploys "$VERSION" new --env staging
```

### 6. Complete Release Script

```bash
#!/bin/bash
# scripts/sentry-release.sh — run after deployment
set -euo pipefail

VERSION="${1:-$(git rev-parse --short HEAD)}"
ENVIRONMENT="${2:-production}"

echo "Creating Sentry release: $VERSION"

# Create release
sentry-cli releases new "$VERSION"

# Associate commits
sentry-cli releases set-commits "$VERSION" --auto

# Upload source maps
sentry-cli sourcemaps upload \
  --release="$VERSION" \
  --url-prefix="~/static/js" \
  --validate \
  ./dist

# Finalize
sentry-cli releases finalize "$VERSION"

# Record deployment
sentry-cli releases deploys "$VERSION" new \
  --env "$ENVIRONMENT"

echo "Release $VERSION deployed to $ENVIRONMENT"
```

### 7. SDK Release Configuration

The SDK `release` option MUST match the CLI release version:

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: process.env.SENTRY_RELEASE, // Same value as CLI $VERSION
  environment: process.env.SENTRY_ENVIRONMENT,
});
```

Inject at build time:
```javascript
// webpack.config.js
const { DefinePlugin } = require('webpack');

module.exports = {
  plugins: [
    new DefinePlugin({
      'process.env.SENTRY_RELEASE': JSON.stringify(process.env.VERSION),
    }),
  ],
};
```

### 8. Webpack/Vite Plugin (Alternative to CLI)

```javascript
// vite.config.ts
import { sentryVitePlugin } from '@sentry/vite-plugin';

export default {
  build: { sourcemap: true },
  plugins: [
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      release: { name: process.env.VERSION },
      sourcemaps: { assets: './dist/**' },
    }),
  ],
};
```

### 9. Manage Releases via API

```bash
# List releases
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/releases/"

# Delete old source maps to manage storage
sentry-cli releases files "$VERSION" delete --all

# Delete a release entirely
sentry-cli releases delete "$VERSION"
```

## Output
- Release created with version identifier tied to git SHA
- Commits associated for suspect commit detection
- Source maps uploaded and validated for stack trace deobfuscation
- Release finalized with deployment timestamp
- SDK release option matching CLI release version

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `error: API request failed: 401` | Invalid or expired auth token | Regenerate at sentry.io/settings/auth-tokens/ with `project:releases` scope |
| Source maps not resolving | URL prefix mismatch | Compare `--url-prefix` with actual script URLs in browser DevTools |
| `No commits found` with `--auto` | No GitHub/GitLab integration | Install integration at sentry.io/settings/integrations/ or use manual commit range |
| Stack traces show minified code | Source maps uploaded after errors occurred | Upload source maps BEFORE deploying — Sentry does not retroactively apply them |
| `release already exists` | Re-creating existing release | Use `sentry-cli releases set-commits` to update, or choose a new version string |

## Resources
- [Release Management CLI](https://docs.sentry.io/cli/releases/)
- [Source Map Upload CLI](https://docs.sentry.io/platforms/javascript/sourcemaps/uploading/cli/)
- [Vite Plugin](https://docs.sentry.io/platforms/javascript/sourcemaps/uploading/vite/)
- [Releases Product](https://docs.sentry.io/product/releases/)
- [Release Health](https://docs.sentry.io/product/releases/health/)
