---
name: vercel-edge-functions
description: |
  Execute Vercel secondary workflow: Edge Functions.
  Use when API routes with minimal latency,
  or configuring build commands and output directories.
  Trigger with phrases like "vercel edge function",
  "deploy edge function with vercel".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, vercel]
---

# Vercel Edge Functions

## Overview
Build and deploy Edge Functions for ultra-low latency at the edge.
Serverless functions that run close to users worldwide.


## Prerequisites
- Completed `vercel-install-auth` setup
- Familiarity with `vercel-deploy-preview`
- Valid API credentials configured

## Instructions

### Step 1: Set Environment Variables
```typescript
await client.env.create(projectId, [
  { key: 'DATABASE_URL', value: dbUrl, target: ['production'] },
  { key: 'API_SECRET', value: secret, target: ['production', 'preview'] },
]);

```

### Step 2: Configure Build Settings
```typescript
await client.projects.update(projectId, {
  buildCommand: 'npm run build',
  outputDirectory: 'dist',
  installCommand: 'npm ci',
  framework: 'astro',
});

```

### Step 3: Verify Configuration
```typescript
const config = await client.projects.get(projectId);
console.log('Build:', config.buildCommand);
console.log('Output:', config.outputDirectory);
console.log('Env vars:', (await client.env.list(projectId)).length);

```

## Output
- Completed Edge Functions execution

- Results from Vercel API

- Success confirmation or error details

## Error Handling
| Aspect | Deploy Preview | Edge Functions |
|--------|------------|------------|
| Use Case | Deploying a preview for a pull request | API routes with minimal latency |
| Complexity | Medium | Medium |
| Performance | Standard | Ultra-fast (<50ms) |

## Examples

### Complete Workflow
```typescript
// Full project setup from scratch
async function setupProject(name: string) {
  const project = await client.projects.create({ name, framework: 'nextjs' });
  await client.env.create(project.id, envVars);
  await client.domains.add(project.id, `${name}.example.com`);
  return project;
}

```

### Error Recovery
```typescript
try {
  await client.env.create(projectId, envVars);
} catch (err) {
  if (err.code === 'env_already_exists') {
    await client.env.update(projectId, envVars); // update instead
  } else {
    throw err;
  }
}

```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel API Reference](https://vercel.com/docs/api)

## Next Steps
For common errors, see `vercel-common-errors`.