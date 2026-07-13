# Step 1: Scheduled Token Sync Workflow

Deep-dive reference for the `figma-ci-integration` skill — extracted from the 'Step 1: Scheduled Token Sync Workflow' step of the workflow.

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
