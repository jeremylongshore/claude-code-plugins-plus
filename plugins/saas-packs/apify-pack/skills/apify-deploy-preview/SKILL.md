---
name: apify-deploy-preview
description: |
  Execute Apify primary workflow: Deploy & Preview.
  Use when deploying a preview for every pull request,
  promoting staging to production, or rolling back a bad deployment.
  Trigger with phrases like "apify deploy",
  "deploy application with apify".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apify]
---

# Apify Deploy & Preview

## Overview
Deploy applications and create preview environments for branches/PRs.
This is the primary workflow — ship code from local to production.


## Prerequisites
- Completed `apify-install-auth` setup

- Understanding of Apify core concepts

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
- Completed Deploy & Preview execution

- Expected results from Apify API

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
- [Apify Documentation](https://docs.apify.com)
- [Apify API Reference](https://docs.apify.com/api)

## Next Steps
For secondary workflow, see `apify-build-configure`.