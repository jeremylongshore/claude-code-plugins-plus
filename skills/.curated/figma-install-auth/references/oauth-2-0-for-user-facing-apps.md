# Step 4: OAuth 2.0 (For User-Facing Apps)

Deep-dive reference for the `figma-install-auth` skill — extracted from the 'Step 4: OAuth 2.0 (For User-Facing Apps)' step of the workflow.

Use OAuth when your app needs to act on behalf of other Figma users.

```typescript
// 1. Redirect user to Figma authorization URL
const authUrl = new URL('https://www.figma.com/oauth');
authUrl.searchParams.set('client_id', process.env.FIGMA_CLIENT_ID!);
authUrl.searchParams.set('redirect_uri', 'https://yourapp.com/auth/callback');
authUrl.searchParams.set('scope', 'file_content:read,file_comments:write');
authUrl.searchParams.set('state', crypto.randomUUID());
authUrl.searchParams.set('response_type', 'code');
// Redirect: res.redirect(authUrl.toString());

// 2. Exchange code for access token (must happen within 30 seconds)
async function exchangeCode(code: string): Promise<string> {
  const res = await fetch('https://api.figma.com/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      redirect_uri: 'https://yourapp.com/auth/callback',
      code,
      grant_type: 'authorization_code',
    }),
  });
  const { access_token, refresh_token, expires_in } = await res.json();
  // Store refresh_token securely for later use
  return access_token;
}

// 3. Refresh expired tokens
async function refreshToken(refreshToken: string): Promise<string> {
  const res = await fetch('https://api.figma.com/v1/oauth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      refresh_token: refreshToken,
    }),
  });
  const { access_token } = await res.json();
  return access_token;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
