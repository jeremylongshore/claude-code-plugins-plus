# Step 1: OAuth 2.0 App Setup

Deep-dive reference for the `figma-enterprise-rbac` skill — extracted from the 'Step 1: OAuth 2.0 App Setup' step of the workflow.

```typescript
// Figma OAuth 2.0 Authorization Code Flow

// 1. Build authorization URL
function getAuthUrl(state: string): string {
  const params = new URLSearchParams({
    client_id: process.env.FIGMA_CLIENT_ID!,
    redirect_uri: process.env.FIGMA_REDIRECT_URI!,
    scope: 'file_content:read,file_comments:write,file_variables:read',
    state,
    response_type: 'code',
  });
  return `https://www.figma.com/oauth?${params}`;
}

// 2. Exchange authorization code for tokens (within 30 seconds!)
async function exchangeCode(code: string): Promise<{
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user_id: string;
}> {
  const res = await fetch('https://api.figma.com/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      redirect_uri: process.env.FIGMA_REDIRECT_URI!,
      code,
      grant_type: 'authorization_code',
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Token exchange failed: ${res.status} ${error}`);
  }

  return res.json();
}

// 3. Refresh expired tokens
async function refreshAccessToken(refreshToken: string): Promise<{
  access_token: string;
  expires_in: number;
}> {
  const res = await fetch('https://api.figma.com/v1/oauth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.FIGMA_CLIENT_ID!,
      client_secret: process.env.FIGMA_CLIENT_SECRET!,
      refresh_token: refreshToken,
    }),
  });

  if (!res.ok) throw new Error(`Token refresh failed: ${res.status}`);
  return res.json();
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
