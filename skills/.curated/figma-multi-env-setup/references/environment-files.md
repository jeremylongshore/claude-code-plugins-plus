# Step 3: Environment Files

Deep-dive reference for the `figma-multi-env-setup` skill — extracted from the 'Step 3: Environment Files' step of the workflow.

```bash
# .env.development
FIGMA_PAT_DEV="figd_dev-token-read-only"
FIGMA_FILE_KEY_DEV="devFileKey123"

# .env.staging
FIGMA_PAT_STAGING="figd_staging-token"
FIGMA_FILE_KEY_STAGING="stagingFileKey456"

# .env.production (stored in secret manager, not in repo)
FIGMA_PAT_PROD="figd_prod-token"
FIGMA_FILE_KEY_PROD="prodFileKey789"
FIGMA_WEBHOOK_PASSCODE="webhook-secret"

# .env.example (committed to repo as template)
FIGMA_PAT_DEV=
FIGMA_FILE_KEY_DEV=
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
