# Notion Enterprise RBAC — Worked Examples

## Full OAuth Integration (Express)

Wires the OAuth start/callback routes, persists the returned workspace token
via `tokenStore`, records an `workspace_authorized` audit entry, and exposes a
`/workspaces` listing endpoint. Assumes `getAuthorizationUrl`,
`exchangeCodeForToken`, `tokenStore`, and `auditLog` from
[the full implementation](implementation.md).

```typescript
import express from 'express';
import session from 'express-session';
import crypto from 'crypto';

const app = express();
app.use(session({ secret: process.env.SESSION_SECRET!, resave: false, saveUninitialized: false }));

app.get('/auth/notion', (req, res) => {
  const state = crypto.randomUUID();
  (req.session as any).oauthState = state;
  res.redirect(getAuthorizationUrl(state));
});

app.get('/auth/notion/callback', async (req, res) => {
  if (req.query.state !== (req.session as any).oauthState) {
    return res.status(403).send('Invalid state');
  }
  const tokenData = await exchangeCodeForToken(req.query.code as string);
  await tokenStore.store(tokenData);

  await auditLog({
    userId: tokenData.owner?.user?.id ?? 'unknown',
    workspaceId: tokenData.bot_id,
    action: 'workspace_authorized',
    resource: { type: 'workspace', id: tokenData.workspace_id },
    result: 'success',
  });

  res.redirect(`/dashboard?workspace=${encodeURIComponent(tokenData.workspace_name)}`);
});

app.get('/workspaces', async (_req, res) => {
  const workspaces = await tokenStore.listWorkspaces();
  res.json(workspaces);
});
```
