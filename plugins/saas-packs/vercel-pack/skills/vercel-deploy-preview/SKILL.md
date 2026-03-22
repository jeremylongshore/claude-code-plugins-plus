---
name: vercel-deploy-preview
description: |
  Execute Vercel primary workflow: Deploy Preview.
  Use when Deploying a preview for a pull request,
  Testing changes before production, or Sharing preview URLs with stakeholders.
  Trigger with phrases like "vercel deploy preview",
  "create preview deployment with vercel".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, vercel]
---

# Vercel Deploy Preview

## Overview
Deploy preview environments for pull requests and branches.
This is the primary workflow for Vercel - instant previews for every commit.


## Prerequisites
- Completed `vercel-install-auth` setup

- Understanding of Vercel core concepts

- Valid API credentials configured

## Instructions

### Step 1: Configure Deployment
```typescript
const deployConfig = {
  project: process.env.PROJECT_ID,
  branch: 'main',
  env: {
    NODE_ENV: 'production',
    API_URL: process.env.API_URL,
  },
};

```

### Step 2: Trigger Deploy
```typescript
const deployment = await client.deployments.create({
  ...deployConfig,
  production: false, // preview first
});
console.log(`Deploy started: ${deployment.url}`);
console.log(`Status: ${deployment.status}`);

```

### Step 3: Monitor and Promote
```typescript
// Wait for build to complete
const result = await client.deployments.wait(deployment.id);
if (result.status === 'ready') {
  console.log(`Preview live at: ${result.url}`);
  // Promote to production when ready
  // await client.deployments.promote(deployment.id);
}

```

## Output
- Completed Deploy Preview execution

- Expected results from Vercel API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Build Failed | Build script exited with non-zero code (dependency or compile error) | Check build logs. Run build locally to reproduce. Fix dependency issues. |
| Deploy Timeout | Build or health check exceeded time limit | Optimize build step, reduce bundle size, or increase timeout setting. |

## Examples

### Complete Workflow
```typescript
// Full deploy pipeline: build → preview → verify → promote
const client = new DevClient({ token: process.env.API_KEY });

const deploy = await client.deployments.create({
  project: 'my-app',
  branch: process.env.GITHUB_REF,
});

const result = await client.deployments.wait(deploy.id);
console.log(`Deployed to: ${result.url} (${result.status})`);

```

### Common Variations
- **Preview per PR**: Auto-deploy on pull_request webhook events
- **Rollback**: Instantly revert to previous deployment by ID
- **Environment promotion**: Deploy to staging first, then promote to production


## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel API Reference](https://vercel.com/docs/api)

## Next Steps
For secondary workflow, see `vercel-edge-functions`.