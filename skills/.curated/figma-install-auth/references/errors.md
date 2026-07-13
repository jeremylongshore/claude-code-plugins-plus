# figma-install-auth: Error Handling

Error reference for the `figma-install-auth` skill — extracted from the skill's Error Handling guidance.

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `403 Forbidden` | 403 | Token lacks required scope | Regenerate PAT with correct scopes |
| `Invalid token` | 403 | Expired or revoked PAT | Generate a new token (90-day max) |
| `OAuth code expired` | 400 | Code exchange took >30s | Retry auth flow; exchange immediately |
| `Invalid redirect_uri` | 400 | Redirect URL mismatch | Must match URL registered in Figma OAuth app settings |
| `Rate limited` | 429 | Too many auth attempts | Wait for `Retry-After` header value |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
