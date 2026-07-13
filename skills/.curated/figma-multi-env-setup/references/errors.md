# figma-multi-env-setup: Error Handling

Error reference for the `figma-multi-env-setup` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong file in dev | Using prod file key | Verify FIGMA_FILE_KEY_DEV |
| PAT expired in CI | 90-day expiry | Set rotation reminder per environment |
| Staging webhook pointing to prod | Wrong endpoint URL | Verify webhook endpoint per env |
| Config not loading | Missing NODE_ENV | Set NODE_ENV in deployment config |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
