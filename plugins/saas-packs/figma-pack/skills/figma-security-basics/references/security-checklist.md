# Step 5: Security Checklist

Deep-dive reference for the `figma-security-basics` skill — extracted from the 'Step 5: Security Checklist' step of the workflow.

```markdown
- [ ] PAT stored in environment variable, not in code
- [ ] `.env` files listed in `.gitignore`
- [ ] Token uses minimum required scopes
- [ ] Token rotation scheduled before 90-day expiry
- [ ] Webhook passcode verified on every incoming request
- [ ] OAuth client secret stored in secret manager (not repo)
- [ ] No tokens in frontend/client-side code
- [ ] Git history scanned for leaked tokens (use `git log -p | grep figd_`)
- [ ] Different tokens for dev/staging/prod environments
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
