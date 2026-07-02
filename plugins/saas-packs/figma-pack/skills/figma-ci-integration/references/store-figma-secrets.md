# Step 4: Store Figma Secrets

Deep-dive reference for the `figma-ci-integration` skill — extracted from the 'Step 4: Store Figma Secrets' step of the workflow.

```bash
# Add PAT as repository secret
gh secret set FIGMA_PAT --body "figd_your-token-here"

# Add file key as repository variable (not secret -- it's not sensitive)
gh variable set FIGMA_FILE_KEY --body "abc123XYZdefaultFileKey"
gh variable set FIGMA_ICON_FILE_KEY --body "def456IconFileKey"
gh variable set FIGMA_ICON_FRAME_ID --body "123:456"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
