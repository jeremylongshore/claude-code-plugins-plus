# Package Manager Policy

**Last Updated:** 2025-12-23
**Status:** Enforced via CI

## Mandatory Package Manager

This repository **exclusively uses pnpm** for package management.

### Why pnpm?

- **Single lockfile:** `pnpm-lock.yaml` is the canonical source of truth
- **Monorepo-optimized:** Efficient workspace handling
- **Reproducible builds:** `--frozen-lockfile` guarantees exact versions
- **Disk space:** Shared content-addressable store
- **Strictness:** Prevents phantom dependencies

### Package Manager Declaration

Root `package.json` includes:

```json
{
  "packageManager": "pnpm@9.15.9"
}
```

This enables **Corepack** to automatically use the correct pnpm version.

## Forbidden Files

The following lockfiles are **prohibited** and will cause CI failures:

- ❌ `package-lock.json` (npm)
- ❌ `yarn.lock` (Yarn)
- ❌ `bun.lockb` (Bun)
- ❌ `bun.lock` (Bun)

**Enforcement:** `scripts/check-package-manager.mjs` runs on every PR and push to `main`.

## Installation Commands

### Local Development

```bash
# Enable Corepack (one-time setup)
corepack enable

# Install all workspace dependencies
pnpm install

# Build all packages
pnpm build

# Build specific workspace package
pnpm -C marketplace build
pnpm -C packages/cli build
```

### CI/CD (GitHub Actions)

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'

- name: Enable Corepack
  run: corepack enable

- name: Install dependencies
  run: pnpm install --frozen-lockfile

- name: Build
  run: pnpm build
```

**Critical:** Always use `--frozen-lockfile` in CI to ensure reproducibility.

## Workspace Commands

This monorepo uses pnpm workspaces:

```yaml
# pnpm-workspace.yaml
packages:
  - 'plugins/mcp/*'
  - 'marketplace'
  - 'packages/cli'
```

### Running Commands

```bash
# Run command in specific workspace
pnpm -C marketplace dev
pnpm -C packages/cli build

# Run command in all workspaces
pnpm --filter '*' build

# Run command in specific workspace by name
pnpm --filter marketplace dev
```

## Deployment: GitHub Pages

The marketplace deploys to GitHub Pages via `.github/workflows/deploy-marketplace.yml`:

- Uses `pnpm install --frozen-lockfile`
- Builds with `pnpm -C marketplace build`
- Deploys `marketplace/dist/` to `gh-pages` branch
- Custom domain: `claudecodeplugins.io` (configured in GitHub UI)

## Publishing: npm Registry

While we build with pnpm, the CLI package publishes to npm registry:

- Build: `pnpm -C packages/cli build`
- Publish: `npm publish --provenance --access public` (from `packages/cli/`)
- Users install via: `npx @claude-code-plugins/ccp doctor`

## Migration from Other Package Managers

If you find npm/yarn/bun lockfiles:

```bash
# Remove forbidden lockfiles
rm package-lock.json yarn.lock bun.lockb bun.lock

# Remove node_modules
rm -rf node_modules marketplace/node_modules

# Reinstall with pnpm
corepack enable
pnpm install
```

## Enforcement Script

`scripts/check-package-manager.mjs` performs automated checks:

1. **Lockfile detection:** Fails if `package-lock.json`, `yarn.lock`, or `bun.lock*` exist
2. **Workflow validation:** Fails if workflows reference `npm install`, `yarn install`, or `bun install` (except in comments or package manager compatibility tests)
3. **Package.json validation:** Ensures `"packageManager": "pnpm@X.X.X"` is present

### Running Locally

```bash
node scripts/check-package-manager.mjs
```

Exit codes:
- `0` = All checks passed
- `1` = Policy violations found

## Support

- **Questions:** Open a GitHub Discussion
- **Policy violations:** CI will fail with specific fix instructions
- **Corepack issues:** Ensure Node.js 18+ and run `corepack enable`

## Version History

- **2025-12-23:** Initial policy (pnpm 9.15.9)
  - Migrated from mixed npm/pnpm usage
  - Standardized all workflows
  - Added enforcement CI check
