---
name: sentry-ci-integration
description: |
  Integrate Sentry with CI/CD pipelines for automated releases.
  Use when setting up GitHub Actions, GitLab CI, or other CI systems
  with Sentry releases and source maps.
  Trigger with phrases like "sentry github actions", "sentry CI",
  "sentry pipeline", "automate sentry releases".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(sentry-cli:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, ci-cd, github-actions, deployment]

---
# Sentry CI Integration

## Prerequisites
- Sentry CLI installed or available in CI
- `SENTRY_AUTH_TOKEN` secret configured in CI platform
- `SENTRY_ORG` and `SENTRY_PROJECT` environment variables
- Source maps generated during build step

## Instructions

### 1. GitHub Actions — Full Release Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy with Sentry Release

on:
  push:
    branches: [main]

env:
  SENTRY_ORG: ${{ secrets.SENTRY_ORG }}
  SENTRY_PROJECT: ${{ secrets.SENTRY_PROJECT }}
  SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full git history for commit association

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Build with source maps
        run: npm run build
        env:
          SENTRY_RELEASE: ${{ github.sha }}

      - name: Create Sentry release
        run: |
          VERSION="${{ github.sha }}"

          # Install Sentry CLI
          npm install -g @sentry/cli

          # Create release
          sentry-cli releases new "$VERSION"

          # Associate commits (requires GitHub integration in Sentry)
          sentry-cli releases set-commits "$VERSION" --auto

          # Upload source maps
          sentry-cli sourcemaps upload \
            --release="$VERSION" \
            --url-prefix="~/static/js" \
            --validate \
            ./dist

          # Finalize release
          sentry-cli releases finalize "$VERSION"

          # Record deployment
          sentry-cli releases deploys "$VERSION" new \
            --env production

      - name: Deploy application
        run: npm run deploy
```

### 2. Using the Official Sentry GitHub Action

```yaml
# Simpler alternative using getsentry/action-release
- name: Create Sentry release
  uses: getsentry/action-release@v1
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: ${{ secrets.SENTRY_ORG }}
    SENTRY_PROJECT: ${{ secrets.SENTRY_PROJECT }}
  with:
    environment: production
    version: ${{ github.sha }}
    sourcemaps: ./dist
    url_prefix: '~/static/js'
    set_commits: auto
```

### 3. GitLab CI Configuration

```yaml
# .gitlab-ci.yml
sentry-release:
  stage: post-deploy
  image: getsentry/sentry-cli:latest
  variables:
    SENTRY_AUTH_TOKEN: $SENTRY_AUTH_TOKEN
    SENTRY_ORG: $SENTRY_ORG
    SENTRY_PROJECT: $SENTRY_PROJECT
  script:
    - VERSION="$CI_COMMIT_SHA"
    - sentry-cli releases new "$VERSION"
    - sentry-cli releases set-commits "$VERSION" --auto
    - sentry-cli sourcemaps upload
        --release="$VERSION"
        --url-prefix="~/static/js"
        ./dist
    - sentry-cli releases finalize "$VERSION"
    - sentry-cli releases deploys "$VERSION" new --env production
  only:
    - main
```

### 4. Inject Release Version at Build Time

```javascript
// webpack.config.js
const { sentryWebpackPlugin } = require('@sentry/webpack-plugin');

module.exports = {
  devtool: 'source-map',
  plugins: [
    sentryWebpackPlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      release: {
        name: process.env.GITHUB_SHA || process.env.CI_COMMIT_SHA,
        setCommits: { auto: true },
        deploy: { env: 'production' },
      },
      sourcemaps: {
        assets: ['./dist/**'],
      },
      // Delete source maps after upload (don't serve to clients)
      sourcemaps: {
        filesToDeleteAfterUpload: ['./dist/**/*.map'],
      },
    }),
  ],
};
```

### 5. CI Environment Variables Setup

```bash
# GitHub Actions — add these as repository secrets:
# Settings > Secrets and variables > Actions
SENTRY_AUTH_TOKEN=sntrys_...     # From sentry.io/settings/auth-tokens/
SENTRY_ORG=my-org                # Organization slug
SENTRY_PROJECT=my-project        # Project slug

# Required token scopes:
# - project:releases (create releases, upload source maps)
# - org:read (read organization data for commit association)
```

### 6. Validate Source Maps in CI

```yaml
# Add validation step before deployment
- name: Validate source maps
  run: |
    # Dry-run upload to validate without sending
    sentry-cli sourcemaps upload \
      --release="${{ github.sha }}" \
      --url-prefix="~/static/js" \
      --validate \
      --dry-run \
      ./dist

    # Verify expected files exist
    if [ ! -f ./dist/main.js.map ]; then
      echo "ERROR: Source maps not generated"
      exit 1
    fi
```

### 7. Monorepo Configuration

For monorepos with multiple Sentry projects:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-api:
    steps:
      - name: Sentry release for API
        env:
          SENTRY_PROJECT: api-backend
        run: |
          VERSION="api@${{ github.sha }}"
          sentry-cli releases new "$VERSION"
          sentry-cli sourcemaps upload --release="$VERSION" ./api/dist
          sentry-cli releases finalize "$VERSION"
          sentry-cli releases deploys "$VERSION" new --env production

  deploy-web:
    steps:
      - name: Sentry release for Web
        env:
          SENTRY_PROJECT: web-frontend
        run: |
          VERSION="web@${{ github.sha }}"
          sentry-cli releases new "$VERSION"
          sentry-cli sourcemaps upload --release="$VERSION" --url-prefix="~/" ./web/dist
          sentry-cli releases finalize "$VERSION"
          sentry-cli releases deploys "$VERSION" new --env production
```

## Output
- GitHub Actions/GitLab CI workflow creating Sentry releases on every deploy
- Source maps uploaded and validated before deployment
- Commits associated for suspect commit detection
- Deploy notifications sent to Sentry with environment
- Release version injected at build time matching SDK config

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `error: API request failed: 401` | Auth token invalid or missing | Verify `SENTRY_AUTH_TOKEN` secret is set and not expired |
| `No commits found` | GitHub/GitLab integration not installed | Install at sentry.io/settings/integrations/ |
| `fetch-depth: 0` missing | Shallow clone breaks commit association | Add `fetch-depth: 0` to checkout step |
| Source maps not resolving | URL prefix mismatch | Compare `--url-prefix` with actual URLs in browser Network tab |
| Release already exists | Re-running workflow | Sentry allows updating existing releases; non-fatal warning |

## Resources
- [Release Automation](https://docs.sentry.io/product/releases/setup/release-automation/)
- [GitHub Action](https://github.com/getsentry/action-release)
- [Webpack Plugin](https://docs.sentry.io/platforms/javascript/sourcemaps/uploading/webpack/)
- [CI/CD Guide](https://docs.sentry.io/cli/releases/)
