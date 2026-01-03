---
name: sentry-release-management
description: |
  Manage Sentry releases and associate commits.
  Use when creating releases, tracking commits,
  or managing release artifacts.
  Trigger with phrases like "sentry release", "sentry commits",
  "manage sentry versions", "sentry release workflow".
allowed-tools: Read, Write, Edit, Bash(sentry-cli:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Release Management

## Overview
Create and manage releases to track errors by version and commit.

## Release Workflow

### 1. Create Release
```bash
# Using git SHA
VERSION=$(git rev-parse --short HEAD)
sentry-cli releases new $VERSION

# Using semantic version
VERSION="1.2.3"
sentry-cli releases new "myapp@$VERSION"

# Using package.json version
VERSION=$(node -p "require('./package.json').version")
sentry-cli releases new "myapp@$VERSION"
```

### 2. Associate Commits
```bash
# Auto-detect commits from git
sentry-cli releases set-commits $VERSION --auto

# Specify commit range
sentry-cli releases set-commits $VERSION \
  --commit "repo-name@from-sha..to-sha"

# Manual commit association
sentry-cli releases set-commits $VERSION \
  --commit "org/repo@abc123"
```

### 3. Upload Artifacts
```bash
# Upload source maps
sentry-cli releases files $VERSION upload-sourcemaps ./dist

# Upload with URL prefix
sentry-cli releases files $VERSION upload-sourcemaps ./dist \
  --url-prefix "~/static/js"

# Upload specific files
sentry-cli releases files $VERSION upload ./dist/app.js.map
```

### 4. Finalize Release
```bash
# Mark release as complete
sentry-cli releases finalize $VERSION

# All-in-one
sentry-cli releases new $VERSION --finalize
```

## Release Naming Strategies

### Git-Based
```bash
# Short SHA (recommended for CD)
VERSION=$(git rev-parse --short HEAD)

# Full SHA
VERSION=$(git rev-parse HEAD)

# Tag-based
VERSION=$(git describe --tags --always)
```

### Semantic Versioning
```typescript
// package.json driven
const version = require('./package.json').version;

Sentry.init({
  release: `myapp@${version}`,
});
```

### Timestamp-Based
```bash
VERSION=$(date +%Y%m%d%H%M%S)
```

## Application Configuration

```typescript
import * as Sentry from '@sentry/node';

// Must match CLI release version
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  release: process.env.SENTRY_RELEASE,
  // Or build-time injection
  release: __SENTRY_RELEASE__, // Webpack DefinePlugin
});
```

### Webpack Configuration
```javascript
// webpack.config.js
const { DefinePlugin } = require('webpack');
const { execSync } = require('child_process');

const release = execSync('git rev-parse --short HEAD').toString().trim();

module.exports = {
  plugins: [
    new DefinePlugin({
      __SENTRY_RELEASE__: JSON.stringify(release),
    }),
  ],
};
```

## Release Management API

### List Releases
```bash
sentry-cli releases list
```

### Delete Release
```bash
sentry-cli releases delete $VERSION
```

### View Release Details
```bash
sentry-cli releases info $VERSION
```

### List Files in Release
```bash
sentry-cli releases files $VERSION list
```

## Commit Integration

### GitHub Integration
1. Install Sentry GitHub App
2. Connect repository
3. Commits auto-linked to releases

### Benefits of Commit Association
- **Suspect commits** - See which commit likely caused an issue
- **Release comparison** - Compare errors between releases
- **Author attribution** - Know who to assign issues to

## Best Practices

### Consistent Naming
```bash
# Good: Predictable, traceable
release: "myapp@1.2.3"
release: "myapp@abc123"

# Bad: Unpredictable
release: "latest"
release: "production"
```

### Source Map Management
```bash
# Delete old source maps
sentry-cli releases files $OLD_VERSION delete --all

# Cleanup old releases
sentry-cli releases delete $OLD_VERSION
```

### Release Script
```bash
#!/bin/bash
# release.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
  VERSION=$(git rev-parse --short HEAD)
fi

echo "Creating release: $VERSION"

sentry-cli releases new $VERSION
sentry-cli releases set-commits $VERSION --auto
sentry-cli releases files $VERSION upload-sourcemaps ./dist
sentry-cli releases finalize $VERSION

echo "Release $VERSION created successfully"
```

## Resources
- [Sentry Releases](https://docs.sentry.io/product/releases/)
- [Sentry CLI Releases](https://docs.sentry.io/product/cli/releases/)
