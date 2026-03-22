---
name: vercel-sdk-patterns
description: |
  Production-ready Vercel REST API patterns with typed fetch wrappers and error handling.
  Use when integrating with the Vercel API programmatically, building deployment tools,
  or establishing team coding standards for Vercel API calls.
  Trigger with phrases like "vercel SDK patterns", "vercel API wrapper",
  "vercel REST API client", "vercel best practices", "idiomatic vercel API".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, api, typescript, patterns]

---
# Vercel SDK Patterns

## Overview
Build a typed, production-ready wrapper around the Vercel REST API (`api.vercel.com`). Covers authentication, pagination, error handling, retry logic, and common endpoint patterns for deployments, projects, and environment variables.

## Prerequisites
- Completed `vercel-install-auth` setup
- TypeScript project with `strict` mode enabled
- Vercel access token with appropriate scope

## Instructions

### Step 1: Create Typed API Client
```typescript
// lib/vercel-client.ts
interface VercelClientConfig {
  token: string;
  teamId?: string;
  baseUrl?: string;
}

interface VercelError {
  error: { code: string; message: string };
}

class VercelClient {
  private token: string;
  private teamId?: string;
  private baseUrl: string;

  constructor(config: VercelClientConfig) {
    this.token = config.token;
    this.teamId = config.teamId;
    this.baseUrl = config.baseUrl ?? 'https://api.vercel.com';
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const url = new URL(path, this.baseUrl);
    if (this.teamId) url.searchParams.set('teamId', this.teamId);

    const res = await fetch(url.toString(), {
      method,
      headers: {
        Authorization: `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const err: VercelError = await res.json();
      throw new VercelApiError(res.status, err.error.code, err.error.message);
    }

    // 204 No Content
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }

  // --- Projects ---
  async listProjects(limit = 20) {
    return this.request<{ projects: VercelProject[] }>(
      'GET', `/v9/projects?limit=${limit}`
    );
  }

  async getProject(idOrName: string) {
    return this.request<VercelProject>('GET', `/v9/projects/${idOrName}`);
  }

  // --- Deployments ---
  async listDeployments(projectId?: string, limit = 20) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (projectId) params.set('projectId', projectId);
    return this.request<{ deployments: VercelDeployment[] }>(
      'GET', `/v6/deployments?${params}`
    );
  }

  async getDeployment(idOrUrl: string) {
    return this.request<VercelDeployment>(
      'GET', `/v13/deployments/${idOrUrl}`
    );
  }

  // --- Environment Variables ---
  async listEnvVars(projectId: string) {
    return this.request<{ envs: VercelEnvVar[] }>(
      'GET', `/v9/projects/${projectId}/env`
    );
  }

  async createEnvVar(projectId: string, envVar: CreateEnvVarInput) {
    return this.request<VercelEnvVar>(
      'POST', `/v9/projects/${projectId}/env`, envVar
    );
  }

  // --- Domains ---
  async listDomains(projectId: string) {
    return this.request<{ domains: VercelDomain[] }>(
      'GET', `/v9/projects/${projectId}/domains`
    );
  }

  async addDomain(projectId: string, domain: string) {
    return this.request<VercelDomain>(
      'POST', `/v9/projects/${projectId}/domains`, { name: domain }
    );
  }
}
```

### Step 2: Define Types
```typescript
// lib/vercel-types.ts
interface VercelProject {
  id: string;
  name: string;
  framework: string | null;
  latestDeployments: VercelDeployment[];
  targets: Record<string, VercelDeployment>;
  createdAt: number;
  updatedAt: number;
}

interface VercelDeployment {
  uid: string;
  name: string;
  url: string;
  state: 'BUILDING' | 'ERROR' | 'INITIALIZING' | 'QUEUED' | 'READY' | 'CANCELED';
  target: 'production' | 'preview' | null;
  createdAt: number;
  buildingAt: number;
  ready: number;
  meta: Record<string, string>;
}

interface VercelEnvVar {
  id: string;
  key: string;
  value: string;
  type: 'system' | 'encrypted' | 'plain' | 'sensitive';
  target: ('production' | 'preview' | 'development')[];
  createdAt: number;
  updatedAt: number;
}

interface CreateEnvVarInput {
  key: string;
  value: string;
  type: 'encrypted' | 'plain' | 'sensitive';
  target: ('production' | 'preview' | 'development')[];
}

interface VercelDomain {
  name: string;
  verified: boolean;
  redirect: string | null;
  gitBranch: string | null;
  createdAt: number;
  updatedAt: number;
}
```

### Step 3: Custom Error Class
```typescript
// lib/vercel-errors.ts
class VercelApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(`Vercel API ${status}: [${code}] ${message}`);
    this.name = 'VercelApiError';
  }

  get isRateLimit(): boolean { return this.status === 429; }
  get isNotFound(): boolean { return this.status === 404; }
  get isUnauthorized(): boolean { return this.status === 401 || this.status === 403; }
}
```

### Step 4: Retry with Exponential Backoff
```typescript
// lib/vercel-retry.ts
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof VercelApiError && err.isRateLimit && attempt < maxRetries) {
        const delay = baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
        console.warn(`Rate limited. Retrying in ${Math.round(delay)}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
  throw new Error('Unreachable');
}

// Usage:
// const projects = await withRetry(() => client.listProjects());
```

### Step 5: Paginated Fetching
```typescript
// lib/vercel-pagination.ts
async function* paginateDeployments(
  client: VercelClient,
  projectId: string,
  pageSize = 100
): AsyncGenerator<VercelDeployment[]> {
  let until: number | undefined;

  while (true) {
    const params = new URLSearchParams({ limit: String(pageSize) });
    if (until) params.set('until', String(until));
    if (projectId) params.set('projectId', projectId);

    const { deployments } = await client.listDeployments(projectId, pageSize);
    if (deployments.length === 0) break;

    yield deployments;
    until = deployments[deployments.length - 1].createdAt;
    if (deployments.length < pageSize) break;
  }
}
```

## API Endpoint Quick Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List projects | GET | `/v9/projects` |
| Get project | GET | `/v9/projects/{idOrName}` |
| Delete project | DELETE | `/v9/projects/{idOrName}` |
| List deployments | GET | `/v6/deployments` |
| Create deployment | POST | `/v13/deployments` |
| Get deployment | GET | `/v13/deployments/{id}` |
| Delete deployment | DELETE | `/v13/deployments/{id}` |
| List env vars | GET | `/v9/projects/{id}/env` |
| Create env var | POST | `/v9/projects/{id}/env` |
| Edit env var | PATCH | `/v9/projects/{id}/env/{envId}` |
| Delete env var | DELETE | `/v9/projects/{id}/env/{envId}` |
| Add domain | POST | `/v9/projects/{id}/domains` |
| Verify domain | POST | `/v9/projects/{id}/domains/{domain}/verify` |
| List teams | GET | `/v2/teams` |

## Output
- Type-safe Vercel API client with full TypeScript coverage
- Custom error class with semantic helpers (isRateLimit, isNotFound)
- Automatic retry with exponential backoff for 429 responses
- Paginated data fetching for large result sets

## Error Handling
| Error | Status | Solution |
|-------|--------|----------|
| `forbidden` | 403 | Token lacks scope — regenerate with correct permissions |
| `not_found` | 404 | Check project/deployment ID is correct |
| `rate_limited` | 429 | Use `withRetry()` wrapper — waits and retries automatically |
| `team_not_found` | 404 | Verify `teamId` parameter matches your team |
| `bad_request` | 400 | Validate request body matches API schema |

## Resources
- [Vercel REST API Reference](https://vercel.com/docs/rest-api)
- [Vercel REST API Endpoints](https://vercel.com/docs/rest-api/reference)
- [Authentication](https://vercel.com/docs/rest-api#creating-an-access-token)

## Next Steps
Proceed to `vercel-deploy-preview` for preview deployment workflows.
