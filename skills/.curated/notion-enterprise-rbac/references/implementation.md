# Notion Enterprise RBAC — Full Implementation

This reference carries the complete, copy-ready implementation for all three
steps of the Notion enterprise RBAC workflow: the OAuth 2.0 authorization flow,
per-workspace token storage with permission-aware API calls, and the
application-level role system with audit logging.

## Step 1: OAuth 2.0 Authorization Flow

Notion uses OAuth 2.0 for public integrations to access external workspaces:

```typescript
import { Client } from '@notionhq/client';
import crypto from 'crypto';

// Step 1: Build the authorization URL
function getAuthorizationUrl(state: string): string {
  const params = new URLSearchParams({
    client_id: process.env.NOTION_OAUTH_CLIENT_ID!,
    response_type: 'code',
    owner: 'user',       // 'user' = user-level token, 'workspace' = workspace-level
    redirect_uri: process.env.NOTION_REDIRECT_URI!,
    state,               // CSRF protection — must verify on callback
  });
  return `https://api.notion.com/v1/oauth/authorize?${params}`;
}

// Step 2: Exchange authorization code for access token
async function exchangeCodeForToken(code: string): Promise<{
  access_token: string;
  bot_id: string;
  workspace_id: string;
  workspace_name: string;
  workspace_icon: string | null;
  owner: { type: string; user?: { id: string; name: string } };
  duplicated_template_id: string | null;
}> {
  const credentials = Buffer.from(
    `${process.env.NOTION_OAUTH_CLIENT_ID}:${process.env.NOTION_OAUTH_CLIENT_SECRET}`
  ).toString('base64');

  const response = await fetch('https://api.notion.com/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${credentials}`,
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: process.env.NOTION_REDIRECT_URI,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`OAuth token exchange failed: ${error.error}`);
  }

  return response.json();
}

// Step 3: Create a Client for a specific workspace
function createWorkspaceClient(accessToken: string): Client {
  return new Client({ auth: accessToken, timeoutMs: 30_000 });
}

// Express route handlers
app.get('/auth/notion', (req, res) => {
  const state = crypto.randomUUID();
  req.session.oauthState = state;
  res.redirect(getAuthorizationUrl(state));
});

app.get('/auth/notion/callback', async (req, res) => {
  // Verify CSRF state
  if (req.query.state !== req.session.oauthState) {
    return res.status(403).send('Invalid state — possible CSRF attack');
  }

  if (req.query.error) {
    return res.status(400).send(`Authorization denied: ${req.query.error}`);
  }

  const tokenData = await exchangeCodeForToken(req.query.code as string);
  await storeWorkspaceToken(tokenData);

  res.redirect(`/dashboard?workspace=${encodeURIComponent(tokenData.workspace_name)}`);
});
```

**Python — OAuth flow:**

```python
import base64
import requests
from notion_client import Client

def exchange_code_for_token(code: str) -> dict:
    credentials = base64.b64encode(
        f"{os.environ['NOTION_OAUTH_CLIENT_ID']}:{os.environ['NOTION_OAUTH_CLIENT_SECRET']}".encode()
    ).decode()

    response = requests.post(
        "https://api.notion.com/v1/oauth/token",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": os.environ["NOTION_REDIRECT_URI"],
        },
    )
    response.raise_for_status()
    return response.json()

def create_workspace_client(access_token: str) -> Client:
    return Client(auth=access_token, timeout_ms=30_000)
```

## Step 2: Token Storage and Permission-Aware API Calls

**Per-workspace token management:**

```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

interface WorkspaceToken {
  botId: string;          // Primary key — unique per installation
  workspaceId: string;
  workspaceName: string;
  accessToken: string;    // MUST be encrypted at rest
  ownerUserId: string;
  authorizedAt: Date;
  lastUsedAt: Date;
}

// In production, use a database with encryption (e.g., AWS KMS, column-level encryption)
class TokenStore {
  private tokens = new Map<string, WorkspaceToken>();

  async store(tokenData: any): Promise<void> {
    const entry: WorkspaceToken = {
      botId: tokenData.bot_id,
      workspaceId: tokenData.workspace_id,
      workspaceName: tokenData.workspace_name,
      accessToken: tokenData.access_token,  // Encrypt before storing!
      ownerUserId: tokenData.owner?.user?.id ?? '',
      authorizedAt: new Date(),
      lastUsedAt: new Date(),
    };
    this.tokens.set(entry.botId, entry);
  }

  async getClient(botId: string): Promise<Client> {
    const token = this.tokens.get(botId);
    if (!token) {
      throw new Error(`No token found for bot ${botId}. User needs to re-authorize.`);
    }
    token.lastUsedAt = new Date();
    return new Client({ auth: token.accessToken, timeoutMs: 30_000 });
  }

  async revoke(botId: string): Promise<void> {
    this.tokens.delete(botId);
  }

  async listWorkspaces(): Promise<{ botId: string; name: string; authorizedAt: Date }[]> {
    return Array.from(this.tokens.values()).map(t => ({
      botId: t.botId,
      name: t.workspaceName,
      authorizedAt: t.authorizedAt,
    }));
  }
}

const tokenStore = new TokenStore();
```

**Permission-aware API calls — handle Notion's page-level permissions:**

```typescript
// Notion returns ObjectNotFound for pages not shared with the integration
// This is NOT the same as the page being deleted
async function safePageAccess(notion: Client, pageId: string) {
  try {
    return await notion.pages.retrieve({ page_id: pageId });
  } catch (error) {
    if (!isNotionClientError(error)) throw error;

    switch (error.code) {
      case APIErrorCode.ObjectNotFound:
        // Page exists but is NOT shared with this integration
        // User needs to share it via the "..." menu > Connections
        console.log(`Page ${pageId} not accessible. Ask user to share via Connections.`);
        return null;

      case APIErrorCode.RestrictedResource:
        // Integration lacks the required capability (read/update/insert/delete)
        console.log(`Integration lacks capability for ${pageId}. Check integration settings.`);
        return null;

      case APIErrorCode.Unauthorized:
        // Token was revoked — user needs to re-authorize
        console.log(`Token revoked. User needs to re-authorize.`);
        return null;

      default:
        throw error;
    }
  }
}

// List all pages accessible to the integration (discovers shared content)
async function discoverAccessiblePages(notion: Client): Promise<string[]> {
  const pageIds: string[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.search({
      filter: { property: 'object', value: 'page' },
      page_size: 100,
      start_cursor: cursor,
    });
    pageIds.push(...response.results.map(r => r.id));
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  return pageIds;
}
```

## Step 3: Application-Level Roles and Audit Logging

**Role-based access control layered on top of Notion permissions:**

```typescript
enum AppRole {
  Admin = 'admin',
  Editor = 'editor',
  Viewer = 'viewer',
}

const ROLE_PERMISSIONS: Record<AppRole, {
  canRead: boolean;
  canWrite: boolean;
  canDelete: boolean;
  canManageIntegration: boolean;
}> = {
  admin:  { canRead: true, canWrite: true, canDelete: true, canManageIntegration: true },
  editor: { canRead: true, canWrite: true, canDelete: false, canManageIntegration: false },
  viewer: { canRead: true, canWrite: false, canDelete: false, canManageIntegration: false },
};

interface AppUser {
  id: string;
  email: string;
  role: AppRole;
  workspaceBotId: string;  // Links to stored workspace token
}

function checkPermission(user: AppUser, action: 'read' | 'write' | 'delete' | 'manage'): boolean {
  const perms = ROLE_PERMISSIONS[user.role];
  switch (action) {
    case 'read': return perms.canRead;
    case 'write': return perms.canWrite;
    case 'delete': return perms.canDelete;
    case 'manage': return perms.canManageIntegration;
  }
}

// Express middleware
function requirePermission(action: 'read' | 'write' | 'delete' | 'manage') {
  return (req: any, res: any, next: any) => {
    if (!checkPermission(req.user, action)) {
      auditLog({
        userId: req.user.id,
        workspaceId: req.user.workspaceBotId,
        action: `${action}_denied`,
        resource: { type: 'endpoint', id: req.path },
        result: 'denied',
      });
      return res.status(403).json({ error: `Requires "${action}" permission` });
    }
    next();
  };
}

// Route examples
app.get('/api/pages/:id', requirePermission('read'), async (req, res) => {
  const notion = await tokenStore.getClient(req.user.workspaceBotId);
  const page = await safePageAccess(notion, req.params.id);
  res.json(page);
});

app.post('/api/pages', requirePermission('write'), async (req, res) => {
  const notion = await tokenStore.getClient(req.user.workspaceBotId);
  const page = await notion.pages.create(req.body);
  res.json(page);
});
```

**Audit logging — write to structured logs and optionally to a Notion database:**

```typescript
interface AuditEntry {
  timestamp: string;
  userId: string;
  workspaceId: string;
  action: string;
  resource: { type: string; id: string };
  result: 'success' | 'denied' | 'error';
  metadata?: Record<string, unknown>;
}

async function auditLog(entry: Omit<AuditEntry, 'timestamp'>): Promise<void> {
  const full: AuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Always log to structured logging (searchable in log aggregator)
  console.log(JSON.stringify({ level: 'audit', ...full }));

  // Optionally write to a Notion audit database
  if (process.env.NOTION_AUDIT_DB_ID) {
    try {
      const notion = await tokenStore.getClient(entry.workspaceId);
      await notion.pages.create({
        parent: { database_id: process.env.NOTION_AUDIT_DB_ID },
        properties: {
          Action: { title: [{ text: { content: entry.action } }] },
          User: { rich_text: [{ text: { content: entry.userId } }] },
          Result: { select: { name: entry.result } },
          Resource: {
            rich_text: [{ text: { content: `${entry.resource.type}:${entry.resource.id}` } }],
          },
          Timestamp: { date: { start: full.timestamp } },
        },
      });
    } catch (error) {
      // Audit log writes should never crash the application
      console.error('Failed to write audit log to Notion:', error);
    }
  }
}

// Handle workspace deauthorization (user removes integration)
async function handleDeauthorization(botId: string): Promise<void> {
  const workspaces = await tokenStore.listWorkspaces();
  const workspace = workspaces.find(w => w.botId === botId);

  if (workspace) {
    await auditLog({
      userId: 'system',
      workspaceId: botId,
      action: 'workspace_deauthorized',
      resource: { type: 'workspace', id: botId },
      result: 'success',
      metadata: { workspaceName: workspace.name },
    });

    await tokenStore.revoke(botId);
  }
}
```
