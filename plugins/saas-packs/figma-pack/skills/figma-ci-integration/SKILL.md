---
name: figma-ci-integration
description: |
  Automate Figma design token sync and asset export in CI/CD pipelines.
  Use when setting up GitHub Actions for Figma, automating icon exports,
  or validating design token changes in pull requests.
  Trigger with phrases like "figma CI", "figma GitHub Actions",
  "automate figma export", "figma CI pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma CI Integration

## Overview
Automate Figma API workflows in CI/CD: sync design tokens on schedule, export assets on PR, and validate design system consistency.

## Prerequisites
- GitHub repository with Actions enabled
- `FIGMA_PAT` stored as GitHub secret
- Design token extraction script (from `figma-core-workflow-a`)

## Instructions

### Step 1: Scheduled Token Sync Workflow
```yaml
# .github/workflows/figma-token-sync.yml
name: Sync Figma Design Tokens

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9am UTC
  workflow_dispatch:          # Manual trigger

jobs:
  sync-tokens:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      - name: Extract tokens from Figma
        env:
          FIGMA_PAT: ${{ secrets.FIGMA_PAT }}
          FIGMA_FILE_KEY: ${{ vars.FIGMA_FILE_KEY }}
        run: node scripts/extract-figma-tokens.mjs

      - name: Check for changes
        id: diff
        run: |
          git diff --quiet src/styles/tokens.css || echo "changed=true" >> $GITHUB_OUTPUT

      - name: Create PR with token updates
        if: steps.diff.outputs.changed == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRANCH="figma/token-sync-$(date +%Y%m%d)"
          git checkout -b "$BRANCH"
          git add src/styles/tokens.css
          git commit -m "chore: sync design tokens from Figma"
          git push origin "$BRANCH"
          gh pr create \
            --title "Sync design tokens from Figma" \
            --body "Automated token sync from Figma file. Review the CSS changes." \
            --label "design-tokens,automated"
```

### Step 2: Asset Export on PR
```yaml
# .github/workflows/figma-asset-export.yml
name: Export Figma Assets

on:
  pull_request:
    paths:
      - 'figma-config.json'  # Trigger when asset config changes

jobs:
  export-assets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci

      - name: Export icons from Figma
        env:
          FIGMA_PAT: ${{ secrets.FIGMA_PAT }}
          FIGMA_FILE_KEY: ${{ vars.FIGMA_ICON_FILE_KEY }}
          FIGMA_ICON_FRAME: ${{ vars.FIGMA_ICON_FRAME_ID }}
        run: node scripts/export-figma-icons.mjs

      - name: Commit exported assets
        run: |
          git add assets/icons/
          if ! git diff --cached --quiet; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git commit -m "chore: export icons from Figma"
            git push
          fi
```

### Step 3: Design System Validation
```yaml
      - name: Validate design tokens
        run: |
          # Check that all CSS custom properties are valid
          node -e "
            const fs = require('fs');
            const css = fs.readFileSync('src/styles/tokens.css', 'utf-8');
            const vars = css.match(/--[\w-]+:/g) || [];
            console.log('Token count:', vars.length);
            if (vars.length < 10) {
              console.error('Too few tokens extracted -- possible Figma API error');
              process.exit(1);
            }
            // Check for duplicate variable names
            const dupes = vars.filter((v, i) => vars.indexOf(v) !== i);
            if (dupes.length > 0) {
              console.error('Duplicate tokens:', dupes);
              process.exit(1);
            }
          "
```

### Step 4: Store Figma Secrets
```bash
# Add PAT as repository secret
gh secret set FIGMA_PAT --body "figd_your-token-here"

# Add file key as repository variable (not secret -- it's not sensitive)
gh variable set FIGMA_FILE_KEY --body "abc123XYZdefaultFileKey"
gh variable set FIGMA_ICON_FILE_KEY --body "def456IconFileKey"
gh variable set FIGMA_ICON_FRAME_ID --body "123:456"
```

## Output
- Scheduled CI job syncing design tokens from Figma
- Asset export triggered by config changes
- Token validation preventing broken deployments
- PR-based workflow for reviewing design changes

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 403 in CI | PAT expired | Rotate secret: `gh secret set FIGMA_PAT` |
| Empty token output | File key wrong | Verify `FIGMA_FILE_KEY` variable |
| Rate limited in CI | Concurrent workflows | Add concurrency group to workflow |
| Stale cache | Node modules cached | Clear with `actions/cache` invalidation |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Figma REST API](https://developers.figma.com/docs/rest-api/)

## Next Steps
For deployment patterns, see `figma-deploy-integration`.
