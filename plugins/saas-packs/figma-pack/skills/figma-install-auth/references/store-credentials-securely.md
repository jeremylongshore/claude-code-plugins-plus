# Step 2: Store Credentials Securely

Deep-dive reference for the `figma-install-auth` skill — extracted from the 'Step 2: Store Credentials Securely' step of the workflow.

```bash
# .env (NEVER commit to git)
FIGMA_PAT="figd_your-personal-access-token"
FIGMA_FILE_KEY="abc123XYZdefaultFileKey"

# .gitignore
.env
.env.local
.env.*.local
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
