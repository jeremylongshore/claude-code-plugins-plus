---
name: hex-hello-world
description: |
  Create a minimal working Hex example.
  Use when starting a new Hex integration, testing your setup,
  or learning basic Hex API patterns.
  Trigger with phrases like "hex hello world", "hex example",
  "hex quick start", "simple hex code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Hello World

## Overview

List projects, trigger a project run, and poll for results using the Hex API. The core workflow is: trigger a run of a published project, poll for completion, then access the results.

## Prerequisites

- Completed `hex-install-auth` setup
- At least one published Hex project

## Instructions

### Step 1: List Projects

```typescript
// hello-hex.ts
import 'dotenv/config';

const TOKEN = process.env.HEX_API_TOKEN!;
const BASE = 'https://app.hex.tech/api/v1';

async function listProjects() {
  const response = await fetch(`${BASE}/projects`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const projects = await response.json();
  for (const p of projects) {
    console.log(`${p.name} (${p.projectId}) — ${p.status}`);
  }
  return projects;
}
```

### Step 2: Trigger a Project Run

```typescript
async function runProject(projectId: string, inputParams?: Record<string, any>) {
  const response = await fetch(`${BASE}/project/${projectId}/run`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      inputParams: inputParams || {},
      updateCacheResult: true,
    }),
  });
  const { runId, projectId: pid, runStatusUrl } = await response.json();
  console.log(`Run started: ${runId}`);
  console.log(`Status URL: ${runStatusUrl}`);
  return { runId, projectId: pid, runStatusUrl };
}
```

### Step 3: Poll for Run Completion

```typescript
async function waitForRun(projectId: string, runId: string, timeoutMs = 300000): Promise<any> {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const response = await fetch(`${BASE}/project/${projectId}/run/${runId}`, {
      headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    const status = await response.json();
    console.log(`Run ${runId}: ${status.status}`);

    if (status.status === 'COMPLETED') return status;
    if (status.status === 'ERRORED' || status.status === 'KILLED') {
      throw new Error(`Run failed: ${status.status}`);
    }

    await new Promise(r => setTimeout(r, 5000)); // Poll every 5s
  }
  throw new Error('Run timed out');
}
```

### Step 4: Complete Flow

```typescript
async function main() {
  const projects = await listProjects();
  if (projects.length === 0) { console.log('No projects found'); return; }

  const project = projects[0];
  const { runId } = await runProject(project.projectId, { date: '2025-01-01' });
  const result = await waitForRun(project.projectId, runId);
  console.log('Run completed:', result);
}

main().catch(console.error);
```

### Step 5: curl Quick Test

```bash
# List projects
curl -s -H "Authorization: Bearer $HEX_API_TOKEN" \
  https://app.hex.tech/api/v1/projects | python3 -m json.tool

# Trigger a run
curl -X POST -H "Authorization: Bearer $HEX_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputParams": {}}' \
  https://app.hex.tech/api/v1/project/PROJECT_ID/run | python3 -m json.tool
```

## Output

- Listed workspace projects with IDs and status
- Triggered project run with optional input parameters
- Polled run status until completion

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401` | Invalid token | Regenerate API token |
| `403` | Read-only token | Create token with "Run projects" scope |
| `404` | Project not found | Verify project ID, ensure it's published |
| Run ERRORED | Project code failed | Check Hex project logs |

## Resources

- [Hex API Reference](https://learn.hex.tech/docs/api/api-reference)
- [Run Project](https://learn.hex.tech/docs/api/api-reference#run-project)

## Next Steps

Proceed to `hex-local-dev-loop` for development workflow.
