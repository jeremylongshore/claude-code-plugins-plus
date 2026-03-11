---
name: replit-deploy-integration
description: |
  Deploy Replit integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Replit-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy replit", "replit Vercel",
  "replit production deploy", "replit Cloud Run", "replit Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Deploy Integration

## Overview
Deploy applications on Replit's hosting platform. Covers Replit Deployments (Static, Autoscale, Reserved VM), configuring `.replit` files, managing secrets, and setting up custom domains.

## Prerequisites
- Replit account with Deployments enabled (Core or Teams plan)
- Application code in a Repl
- Custom domain (optional) with DNS access
- Replit CLI or web dashboard access

## Instructions

### Step 1: Configure .replit File
```toml
# .replit
run = "npm start"
entrypoint = "index.js"

[deployment]
run = ["sh", "-c", "npm start"]
deploymentTarget = "autoscale"

[nix]
channel = "stable-24_05"

[env]
NODE_ENV = "production"
PORT = "3000"  # 3000: 3 seconds in ms
```

### Step 2: Set Secrets
```markdown
1. Open your Repl in Replit
2. Click the lock icon (Secrets) in the sidebar
3. Add each secret:
   - Key: API_KEY, Value: your-api-key
   - Key: DATABASE_URL, Value: your-db-url
```

```bash
# Or via Replit CLI
replit secrets set API_KEY "your-api-key"
replit secrets set DATABASE_URL "your-db-url"
```

### Step 3: Deploy
```markdown
1. Click "Deploy" button in the Replit editor
2. Choose deployment type:
   - **Static**: For frontend-only apps (free)
   - **Autoscale**: Scales to zero, pay per request
   - **Reserved VM**: Always-on, fixed monthly cost
3. Configure machine size (0.25 - 8 vCPU)
4. Click "Deploy"
```

### Step 4: Custom Domain Setup
```markdown
1. Go to Deployment settings > Custom Domain
2. Enter your domain: app.example.com
3. Add DNS records:
   - CNAME: app -> your-repl.replit.app
4. Wait for SSL certificate provisioning
```

### Step 5: Health Check Endpoint
```typescript
// health.ts
export async function GET() {
  return Response.json({
    status: "healthy",
    environment: process.env.REPL_SLUG,
    region: process.env.REPLIT_DEPLOYMENT_REGION,
    timestamp: new Date().toISOString(),
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy fails | Build error | Check console logs in Replit |
| Port mismatch | Wrong PORT | Use `process.env.PORT` or 3000 |
| Cold start slow | Autoscale spin-up | Use Reserved VM for latency-sensitive apps |
| Secret not found | Not set in Secrets | Add secret via Replit sidebar |

## Examples

### Quick Deploy via CLI
```bash
set -euo pipefail
# Install Replit CLI
npm install -g replit

# Deploy current repl
replit deploy --type autoscale
```

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Secrets](https://docs.replit.com/programming-ide/storing-sensitive-information)
- [Custom Domains](https://docs.replit.com/hosting/custom-domains)

## Next Steps
For multi-environment setup, see `replit-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale