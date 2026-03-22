---
name: vercel-deploy-preview
description: |
  Create and manage Vercel preview deployments for branches and pull requests.
  Use when deploying a preview for a pull request, testing changes before production,
  or sharing preview URLs with stakeholders.
  Trigger with phrases like "vercel deploy preview", "vercel preview URL",
  "create preview deployment", "vercel PR preview".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(curl:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, deployment, preview, workflow]

---
# Vercel Deploy Preview

## Overview
Deploy preview environments for branches and pull requests. Every `git push` to a non-production branch generates a unique preview URL. Covers CLI-based previews, API-based previews, deployment protection, and comment integration.

## Prerequisites
- Completed `vercel-install-auth` setup
- Project linked via `vercel link`
- Git repository connected in Vercel dashboard

## Instructions

### Step 1: Deploy Preview via CLI
```bash
# Deploy current directory to a preview URL (default — not --prod)
vercel

# Output:
# 🔗 Linked to your-team/my-app
# 🔍 Inspect: https://vercel.com/your-team/my-app/AbCdEfG
# ✅ Preview: https://my-app-git-feature-branch-your-team.vercel.app

# Deploy a specific directory
vercel ./dist

# Deploy and wait for build to complete (useful in CI)
vercel --no-wait  # returns immediately with deployment URL
```

### Step 2: Deploy Preview via REST API
```bash
# Create a deployment via API — useful for custom CI pipelines
curl -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "target": "preview",
    "gitSource": {
      "type": "github",
      "repoId": "123456789",
      "ref": "feature/new-feature",
      "sha": "abc123def456"
    }
  }'
```

### Step 3: Check Deployment Status
```bash
# Poll deployment status until READY
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/dpl_xxxxxxxxxxxx" \
  | jq '{state: .state, url: .url, readyState: .readyState}'

# States: QUEUED → BUILDING → READY (or ERROR/CANCELED)
```

```typescript
// Programmatic polling
async function waitForDeployment(client: VercelClient, deploymentId: string) {
  while (true) {
    const d = await client.getDeployment(deploymentId);
    if (d.state === 'READY') return d;
    if (d.state === 'ERROR' || d.state === 'CANCELED') {
      throw new Error(`Deployment ${d.state}: ${deploymentId}`);
    }
    await new Promise(r => setTimeout(r, 5000)); // poll every 5s
  }
}
```

### Step 4: Configure Preview Environment Variables
```bash
# Add env vars scoped to preview only
vercel env add DATABASE_URL preview
# Enter value when prompted

# Or via API — scope to preview environment
curl -X POST "https://api.vercel.com/v9/projects/my-app/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "DATABASE_URL",
    "value": "postgres://preview-db:5432/myapp",
    "type": "encrypted",
    "target": ["preview"]
  }'
```

### Step 5: Deployment Protection
Vercel supports password-protecting preview deployments:

```json
// vercel.json — require authentication for previews
{
  "deploymentProtection": {
    "preview": "vercel-authentication"
  }
}
```

Options:
- `"vercel-authentication"` — requires Vercel team login
- `"standard-protection"` — bypass for automation with `x-vercel-protection-bypass` header
- Disabled — previews are publicly accessible

### Step 6: GitHub Integration — PR Comments
When a GitHub repo is connected, Vercel automatically:
1. Creates a preview deployment on every push
2. Posts a comment on the PR with the preview URL
3. Updates the GitHub commit status (pending → success/failure)
4. Adds "Visit Preview" link in the PR checks section

To configure in the Vercel dashboard:
- **Settings > Git > Deploy Hooks** for manual triggers
- **Settings > Git > Ignored Build Step** to skip builds for certain paths

```bash
# Ignored Build Step — skip deploy when only docs changed
# vercel.json
{
  "ignoreCommand": "git diff HEAD^ HEAD --quiet -- . ':!docs' ':!*.md'"
}
```

## Preview URL Patterns

| Branch | URL Pattern |
|--------|-------------|
| `feature/auth` | `my-app-git-feature-auth-team.vercel.app` |
| `fix/bug-123` | `my-app-git-fix-bug-123-team.vercel.app` |
| Random deploy | `my-app-abc123def.vercel.app` |

## Output
- Preview deployment URL unique to each branch/commit
- Build logs accessible via Vercel dashboard or API
- PR comment with preview link (GitHub integration)
- Environment variables scoped to preview only

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `BUILD_FAILED` | Build command failed | Check build logs: `vercel inspect <url>` |
| `FUNCTION_INVOCATION_FAILED` | Runtime error in function | Review function logs: `vercel logs <url>` |
| `NO_BUILDS` | No output detected | Verify `outputDirectory` in vercel.json |
| Preview not updating | Cached old deployment | Force rebuild: `vercel --force` |
| `DEPLOYMENT_BLOCKED` | Deployment protection active | Use `x-vercel-protection-bypass` header |

## Resources
- [Preview Deployments](https://vercel.com/docs/deployments/preview-deployments)
- [Deployment Protection](https://vercel.com/docs/security/deployment-protection)
- [CLI Deploy Command](https://vercel.com/docs/cli/deploy)
- [REST API: Create Deployment](https://vercel.com/docs/rest-api/deployments/create-a-new-deployment)

## Next Steps
For edge function development, see `vercel-edge-functions`.
