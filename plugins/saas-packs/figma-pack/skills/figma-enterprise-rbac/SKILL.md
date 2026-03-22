---
name: figma-enterprise-rbac
description: |
  Configure Figma Enterprise features: OAuth 2.0, team management, and access control.
  Use when implementing OAuth flows, managing team/project access via API,
  or building Enterprise-level Figma integrations.
  Trigger with phrases like "figma enterprise", "figma OAuth",
  "figma team management", "figma access control", "figma SCIM".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Enterprise RBAC

## Overview
Figma Enterprise features accessible via the REST API: OAuth 2.0 for user-facing apps, team/project management, and the Variables API (Enterprise-only). This skill covers building OAuth integrations and managing organizational access.

## Prerequisites
- Figma Enterprise or Organization plan
- OAuth app registered in Figma developer dashboard
- Understanding of OAuth 2.0 authorization code flow

## Instructions

### Step 1: OAuth 2.0 App Setup
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

### Step 2: OAuth Callback Handler
```typescript
// Express callback handler
app.get('/auth/figma/callback', async (req, res) => {
  const { code, state } = req.query;

  // Verify state matches what we sent (CSRF protection)
  if (state !== req.session.oauthState) {
    return res.status(403).json({ error: 'Invalid state parameter' });
  }

  try {
    // Exchange code within 30 seconds
    const tokens = await exchangeCode(code as string);

    // Get user info with the new token
    const userRes = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': tokens.access_token },
    });
    const user = await userRes.json();

    // Store tokens securely (encrypted at rest)
    await saveUserTokens(user.id, {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresAt: new Date(Date.now() + tokens.expires_in * 1000),
    });

    res.redirect('/dashboard?connected=figma');
  } catch (error) {
    console.error('Figma OAuth error:', error);
    res.redirect('/settings?error=figma_auth_failed');
  }
});
```

### Step 3: Team and Project Management
```typescript
// GET /v1/teams/:team_id/projects -- list team projects
async function getTeamProjects(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/projects`,
    { headers: { 'X-Figma-Token': token } }
  );
  return res.json(); // { projects: [{ id, name }] }
}

// GET /v1/projects/:project_id/files -- list project files
async function getProjectFiles(projectId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/projects/${projectId}/files`,
    { headers: { 'X-Figma-Token': token } }
  );
  return res.json(); // { files: [{ key, name, thumbnail_url, last_modified }] }
}

// GET /v1/teams/:team_id/components -- published components (Tier 3)
async function getTeamComponents(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/components`,
    { headers: { 'X-Figma-Token': token } }
  );
  return res.json();
  // { meta: { components: [{ key, file_key, node_id, name, description }] } }
}

// GET /v1/teams/:team_id/styles -- published styles (Tier 3)
async function getTeamStyles(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/styles`,
    { headers: { 'X-Figma-Token': token } }
  );
  return res.json();
  // { meta: { styles: [{ key, file_key, node_id, name, style_type }] } }
}
```

### Step 4: Variables API (Enterprise Only)
```typescript
// GET /v1/files/:key/variables/local -- Tier 2, requires file_variables:read
async function getLocalVariables(fileKey: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables/local`,
    { headers: { 'X-Figma-Token': token } }
  );
  if (res.status === 403) {
    throw new Error('Variables API requires Figma Enterprise plan');
  }
  return res.json();
  // { meta: { variables: Record<id, Variable>, variableCollections: Record<id, Collection> } }
}

// GET /v1/files/:key/variables/published -- published variables
async function getPublishedVariables(fileKey: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables/published`,
    { headers: { 'X-Figma-Token': token } }
  );
  return res.json();
  // Published variables have a subscribed_id that changes each publish
}

// POST /v1/files/:key/variables -- bulk create/update/delete
async function updateVariables(
  fileKey: string,
  changes: VariableChanges,
  token: string
) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/variables`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': token,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(changes),
    }
  );
  return res.json();
}
```

### Step 5: Access Control Middleware
```typescript
// Middleware that checks if user has Figma access to a resource
async function requireFigmaAccess(fileKey: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userToken = await getUserFigmaToken(req.user.id);
    if (!userToken) {
      return res.status(403).json({ error: 'Figma account not connected' });
    }

    // Check if user's token can access this file
    const check = await fetch(
      `https://api.figma.com/v1/files/${fileKey}?depth=1`,
      { headers: { 'X-Figma-Token': userToken } }
    );

    if (check.status === 403) {
      return res.status(403).json({ error: 'No access to this Figma file' });
    }

    next();
  };
}
```

## Output
- OAuth 2.0 flow with authorization, token exchange, and refresh
- Team/project/file listing via API
- Variables API access (Enterprise)
- Access control middleware for file-level permissions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| OAuth code expired | Exchange took >30s | Exchange immediately on callback |
| Token refresh failed | Refresh token revoked | Re-authenticate user through OAuth flow |
| 403 on Variables API | Not Enterprise plan | Use styles API instead (available on all plans) |
| Team components empty | No published components | Publish components in Figma first |

## Resources
- [Figma OAuth 2.0](https://developers.figma.com/docs/rest-api/authentication/)
- [Figma Variables API](https://developers.figma.com/docs/rest-api/variables-endpoints/)
- [Component Endpoints](https://developers.figma.com/docs/rest-api/component-endpoints/)

## Next Steps
For major migrations, see `figma-migration-deep-dive`.
