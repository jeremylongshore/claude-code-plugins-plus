---
name: hex-local-dev-loop
description: |
  Configure Hex local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Hex.
  Trigger with phrases like "hex dev setup", "hex local development",
  "hex dev environment", "develop with hex".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Local Dev Loop

## Overview

Set up a development workflow for Hex API orchestration with mocked API responses and testing.

## Instructions

### Step 1: Project Structure

```
hex-orchestrator/
├── src/hex/
│   ├── client.ts       # API client
│   ├── orchestrator.ts # Pipeline runner
│   └── types.ts        # TypeScript interfaces
├── tests/
│   ├── fixtures/       # Mock API responses
│   └── orchestrator.test.ts
├── .env.local
└── package.json
```

### Step 2: Typed Hex Client

```typescript
// src/hex/client.ts
export class HexClient {
  constructor(private token: string, private baseUrl = 'https://app.hex.tech/api/v1') {}

  async listProjects() {
    return this.get('/projects');
  }

  async runProject(projectId: string, inputParams?: Record<string, any>) {
    return this.post(`/project/${projectId}/run`, { inputParams: inputParams || {}, updateCacheResult: true });
  }

  async getRunStatus(projectId: string, runId: string) {
    return this.get(`/project/${projectId}/run/${runId}`);
  }

  async cancelRun(projectId: string, runId: string) {
    return this.delete(`/project/${projectId}/run/${runId}`);
  }

  private async get(path: string) {
    const res = await fetch(`${this.baseUrl}${path}`, { headers: { 'Authorization': `Bearer ${this.token}` } });
    if (!res.ok) throw new Error(`Hex API ${res.status}`);
    return res.json();
  }

  private async post(path: string, body: any) {
    const res = await fetch(`${this.baseUrl}${path}`, { method: 'POST', headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) throw new Error(`Hex API ${res.status}`);
    return res.json();
  }

  private async delete(path: string) {
    const res = await fetch(`${this.baseUrl}${path}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${this.token}` } });
    return res.ok;
  }
}
```

### Step 3: Mocked Tests

```typescript
import { describe, it, expect, vi } from 'vitest';
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('HexClient', () => {
  it('should list projects', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{ projectId: 'p1', name: 'Test' }] });
    const client = new HexClient('test-token');
    const projects = await client.listProjects();
    expect(projects).toHaveLength(1);
  });

  it('should trigger a run', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ runId: 'r1', projectId: 'p1' }) });
    const client = new HexClient('test-token');
    const run = await client.runProject('p1', { date: '2025-01-01' });
    expect(run.runId).toBe('r1');
  });
});
```

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)

## Next Steps

See `hex-sdk-patterns` for production patterns.
