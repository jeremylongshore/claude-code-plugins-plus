# Step 2: Asset Export on PR

Deep-dive reference for the `figma-ci-integration` skill — extracted from the 'Step 2: Asset Export on PR' step of the workflow.

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
