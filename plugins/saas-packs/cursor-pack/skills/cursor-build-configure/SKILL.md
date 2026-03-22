---
name: cursor-build-configure
description: |
  Execute Cursor secondary workflow: Build & Configure.
  Use when setting environment variables for different stages,
  or configuring build commands and output directories.
  Trigger with phrases like "cursor configure",
  "configure project with cursor".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Build & Configure

## Overview
Configure project settings, environment variables, and build pipelines.
The setup workflow that makes deployments reproducible.


## Prerequisites
- Completed `cursor-install-auth` setup
- Familiarity with `cursor-deploy-preview`
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
- Completed Build & Configure execution

- Results from Cursor API

- Success confirmation or error details

## Error Handling
| Aspect | Deploy & Preview | Build & Configure |
|--------|------------|------------|
| Use Case | deploying a preview for every pull request | setting environment variables for different stages |
| Complexity | Medium | Low |
| Performance | Standard | Instant (API calls only) |

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
- [Cursor Documentation](https://docs.cursor.com)
- [Cursor API Reference](https://docs.cursor.com/api)

## Next Steps
For common errors, see `cursor-common-errors`.