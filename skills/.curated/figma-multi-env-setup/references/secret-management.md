# Step 4: Secret Management

Deep-dive reference for the `figma-multi-env-setup` skill — extracted from the 'Step 4: Secret Management' step of the workflow.

```bash
# GitHub Actions -- use environment-scoped secrets
gh secret set FIGMA_PAT_PROD --env production --body "figd_..."
gh secret set FIGMA_PAT_STAGING --env staging --body "figd_..."

# Google Cloud Secret Manager
echo -n "figd_prod-token" | gcloud secrets create figma-pat-prod --data-file=-
echo -n "figd_staging-token" | gcloud secrets create figma-pat-staging --data-file=-

# Load in Cloud Run
gcloud run deploy my-service \
  --set-secrets="FIGMA_PAT_PROD=figma-pat-prod:latest"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
