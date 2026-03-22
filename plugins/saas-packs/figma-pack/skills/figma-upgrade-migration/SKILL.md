---
name: figma-upgrade-migration
description: |
  Handle Figma REST API scope changes, deprecations, and migration tasks.
  Use when migrating from deprecated scopes, updating webhook versions,
  or adapting to Figma API changelog changes.
  Trigger with phrases like "upgrade figma", "figma deprecation",
  "figma scope migration", "figma API changes", "figma v2 webhooks".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Upgrade & Migration

## Overview
Handle Figma REST API deprecations and breaking changes. The most significant recent change is the deprecation of the `files:read` scope in favor of granular scopes, and the move from Webhooks V1 to V2.

## Prerequisites
- Current Figma integration working
- Git for version control
- Access to Figma developer settings

## Instructions

### Step 1: Scope Migration (files:read Deprecation)
The `files:read` scope is deprecated. Migrate to granular scopes:

| Deprecated Scope | Replacement Scopes | Endpoints Covered |
|-----------------|-------------------|-------------------|
| `files:read` | `file_content:read` | `GET /v1/files/:key`, `GET /v1/images/:key` |
| `files:read` | `file_comments:read` | `GET /v1/files/:key/comments` |
| `files:read` | `file_dev_resources:read` | `GET /v1/files/:key/dev_resources` |
| `files:read` | `file_versions:read` | `GET /v1/files/:key/versions` |

**Migration steps:**
1. Audit which endpoints your code calls
2. Map each endpoint to its required scope
3. Generate a new PAT with granular scopes
4. Update OAuth apps with new scope list
5. Test all endpoints with the new token
6. Revoke old tokens

```bash
# Find all Figma API calls in your codebase
grep -rn "api.figma.com" --include="*.ts" --include="*.js" src/ \
  | grep -oP '/v\d/[a-z_/]+' | sort -u

# Example output:
# /v1/files
# /v1/files/comments
# /v1/images
# /v2/webhooks
```

### Step 2: Webhooks V1 to V2 Migration
```typescript
// V1 (deprecated): POST /v1/webhooks
// V2 (current):    POST /v2/webhooks

// V2 adds context support: attach webhooks to teams, files, or projects
interface WebhookV2Config {
  event_type: 'FILE_UPDATE' | 'FILE_DELETE' | 'FILE_VERSION_UPDATE'
    | 'FILE_COMMENT' | 'LIBRARY_PUBLISH';
  // Context: where to listen
  team_id?: string;      // team-level (all files in team)
  // OR specify project/file context in the endpoint path
  endpoint: string;      // Your HTTPS webhook URL
  passcode: string;      // Secret for verification
  description?: string;
}

// Create a V2 webhook
async function createWebhook(config: WebhookV2Config) {
  const res = await fetch('https://api.figma.com/v2/webhooks', {
    method: 'POST',
    headers: {
      'X-Figma-Token': process.env.FIGMA_PAT!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error(`Webhook creation failed: ${res.status}`);
  return res.json();
}

// List existing webhooks
async function listWebhooks(teamId: string) {
  const res = await fetch(
    `https://api.figma.com/v2/webhooks?team_id=${teamId}`,
    { headers: { 'X-Figma-Token': process.env.FIGMA_PAT! } }
  );
  return res.json();
}
```

### Step 3: OAuth App Publishing Flow
All OAuth apps (public and private) must complete the new publishing flow:

1. Go to your app in the Figma developer dashboard
2. Complete the required app information fields
3. Add required redirect URLs
4. Submit for review (public apps) or activate (private apps)
5. Update your code to handle the new token format

```typescript
// Check if your OAuth tokens need refresh
async function checkTokenHealth(accessToken: string): Promise<boolean> {
  const res = await fetch('https://api.figma.com/v1/me', {
    headers: { 'X-Figma-Token': accessToken },
  });
  if (res.status === 403) {
    console.warn('Token expired or revoked -- refresh needed');
    return false;
  }
  return res.ok;
}
```

### Step 4: Audit and Update Codebase
```typescript
// Create a migration checker
function auditFigmaIntegration(codebasePaths: string[]) {
  const issues: string[] = [];

  // Check for deprecated scope usage
  // Check for V1 webhook endpoints
  // Check for old token format
  const patterns = [
    { pattern: 'files:read', message: 'Deprecated scope: use file_content:read' },
    { pattern: '/v1/webhooks', message: 'V1 webhooks: migrate to /v2/webhooks' },
    { pattern: 'X-FIGMA-TOKEN', message: 'Header is case-sensitive: use X-Figma-Token' },
  ];

  return { issues, patterns };
}
```

## Output
- Scopes migrated from `files:read` to granular alternatives
- Webhooks upgraded from V1 to V2
- OAuth app publishing flow completed
- All endpoints tested with new tokens

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 403 after scope change | Missing required scope | Add the specific scope for each endpoint |
| Webhook not firing | V1 webhook still active | Delete V1, create V2 webhook |
| OAuth flow broken | Publishing flow not completed | Complete app publishing in dashboard |
| Token format mismatch | Old token type | Generate new PAT with `figd_` prefix |

## Resources
- [Figma REST API Changelog](https://developers.figma.com/docs/rest-api/changelog/)
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)
- [Webhooks V2 Documentation](https://developers.figma.com/docs/rest-api/webhooks/)

## Next Steps
For CI integration during upgrades, see `figma-ci-integration`.
