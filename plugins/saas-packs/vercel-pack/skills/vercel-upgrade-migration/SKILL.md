---
name: vercel-upgrade-migration
description: |
  Upgrade Vercel CLI, Node.js runtime, and Next.js framework versions with breaking change detection.
  Use when upgrading Vercel CLI versions, migrating Node.js runtimes,
  or updating Next.js between major versions on Vercel.
  Trigger with phrases like "upgrade vercel", "vercel migration",
  "vercel breaking changes", "update vercel CLI", "next.js upgrade on vercel".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(npm:*), Bash(npx:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, migration, upgrade]

---
# Vercel Upgrade Migration

## Overview
Safely upgrade Vercel CLI, Node.js runtime versions, and framework versions (especially Next.js) on Vercel. Covers breaking change detection, vercel.json schema changes, and rollback strategy.

## Current State
!`vercel --version 2>/dev/null || echo 'Vercel CLI not installed'`
!`node --version 2>/dev/null || echo 'N/A'`
!`cat package.json 2>/dev/null | jq -r '.dependencies.next // "no next.js"' 2>/dev/null || echo 'N/A'`

## Prerequisites
- Current Vercel CLI installed
- Git for version control
- Test suite available
- Preview deployment for testing

## Instructions

### Step 1: Check Current Versions
```bash
# Current CLI version
vercel --version

# Current Node.js runtime on Vercel
cat package.json | jq '.engines.node'
# Or check vercel.json
cat vercel.json | jq '.functions'

# Check for available CLI updates
npm outdated -g vercel

# Check framework version
npm ls next react
```

### Step 2: Upgrade Vercel CLI
```bash
# Upgrade to latest
npm install -g vercel@latest

# Or specific version
npm install -g vercel@39

# Verify
vercel --version
```

**CLI breaking changes to watch for:**
- v28+: `vercel env pull` output format changed
- v32+: `vercel dev` uses new function runtime
- v37+: `vercel.json` `builds` property deprecated in favor of framework detection

### Step 3: Upgrade Node.js Runtime
```json
// package.json — specify the Node.js version
{
  "engines": {
    "node": "20.x"
  }
}
```

Available runtimes on Vercel:
| Runtime | Status | EOL |
|---------|--------|-----|
| Node.js 18.x | Supported | April 2025 |
| Node.js 20.x | Active LTS (recommended) | April 2026 |
| Node.js 22.x | Current | October 2027 |

```bash
# Test locally with the target Node version first
nvm use 20
npm test
npm run build
```

### Step 4: Upgrade Next.js on Vercel
```bash
# Use the Next.js upgrade codemod
npx @next/codemod@latest upgrade

# Or manual upgrade
npm install next@latest react@latest react-dom@latest

# Check for breaking changes
npx @next/codemod --dry-run
```

**Key Next.js migration points:**
- **13 → 14**: App Router stable, Turbopack available, Server Actions stable
- **14 → 15**: `fetch` no longer cached by default, `cookies()` is async, `NextRequest.geo` removed (use `geolocation()` from `@vercel/functions`)
- **vercel.json changes**: `rewrites`/`redirects` in `next.config.js` take precedence over `vercel.json`

### Step 5: Test in Preview Before Production
```bash
# Create a branch for the upgrade
git checkout -b upgrade/vercel-cli-39

# Make changes and push
git add -A && git commit -m "chore: upgrade vercel CLI and Node.js 20"
git push -u origin upgrade/vercel-cli-39

# Vercel auto-deploys a preview — test it
vercel ls | head -3
curl -s https://my-app-git-upgrade-vercel-cli-39-team.vercel.app/api/health

# Run full test suite against preview
npm test -- --env=preview
```

### Step 6: Rollback Strategy
```bash
# If the upgrade breaks production — instant rollback
vercel rollback

# Pin to a specific CLI version in CI
# .github/workflows/deploy.yml
# - run: npm install -g vercel@38  # pin to known good version

# Revert Node.js runtime
# Change engines.node back in package.json
# Push and redeploy
```

## vercel.json Schema Migration

Deprecated `builds` property (v2 → current):
```json
// Old (deprecated):
{
  "builds": [
    { "src": "api/**/*.ts", "use": "@vercel/node" }
  ]
}

// New (framework auto-detection):
{
  "functions": {
    "api/**/*.ts": {
      "runtime": "nodejs20.x",
      "maxDuration": 30
    }
  }
}
```

## Output
- Vercel CLI upgraded to latest version
- Node.js runtime version updated in package.json
- Framework upgraded with codemods applied
- Preview deployment tested before production promotion
- Rollback strategy documented

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Build failed` after Node upgrade | Dependency incompatible with new Node | Check `npm ls` for native modules, rebuild |
| `Module not found` after Next.js upgrade | Import paths changed | Run `npx @next/codemod` for automatic fixes |
| `vercel.json` validation error | Schema changed in new CLI version | Remove deprecated `builds`, use `functions` |
| `FUNCTION_INVOCATION_FAILED` | Runtime API removed in new Node.js | Check Node.js changelog for removed APIs |
| Preview works but prod fails | Env vars differ between environments | Verify production env vars match preview |

## Resources
- [Vercel CLI Changelog](https://github.com/vercel/vercel/releases)
- [Node.js Runtime on Vercel](https://vercel.com/docs/functions/runtimes/node-js)
- [Next.js Upgrade Guide](https://nextjs.org/docs/app/building-your-application/upgrading)
- [vercel.json Reference](https://vercel.com/docs/project-configuration)

## Next Steps
For CI/CD integration, see `vercel-ci-integration`.
