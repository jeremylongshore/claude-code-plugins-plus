# Step 3: Token Rotation

Deep-dive reference for the `figma-security-basics` skill — extracted from the 'Step 3: Token Rotation' step of the workflow.

```bash
# PATs have a maximum 90-day lifetime
# Schedule rotation before expiry

# 1. Generate new token in Figma Settings > Personal access tokens
# 2. Test new token
curl -s -H "X-Figma-Token: ${NEW_TOKEN}" \
  https://api.figma.com/v1/me | jq '.handle'

# 3. Update environment
# For CI: gh secret set FIGMA_PAT --body "${NEW_TOKEN}"
# For production: update your secret manager

# 4. Verify old token is revoked in Figma Settings
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
