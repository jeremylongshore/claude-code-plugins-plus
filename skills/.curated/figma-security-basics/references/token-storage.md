# Step 1: Token Storage

Deep-dive reference for the `figma-security-basics` skill — extracted from the 'Step 1: Token Storage' step of the workflow.

```bash
# .env (NEVER commit)
FIGMA_PAT="figd_your-personal-access-token"
FIGMA_OAUTH_CLIENT_SECRET="your-oauth-secret"

# .gitignore
.env
.env.local
.env.*.local
*.pem
```

```typescript
// Validate token exists before any API call
function getToken(): string {
  const token = process.env.FIGMA_PAT;
  if (!token) throw new Error('FIGMA_PAT is not set');
  if (!token.startsWith('figd_')) {
    console.warn('Token does not have expected figd_ prefix');
  }
  return token;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
