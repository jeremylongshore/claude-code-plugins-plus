---
name: clickup-sdk-patterns
description: |
  Production-ready ClickUp API v2 client patterns with typed wrappers,
  error handling, caching, and multi-tenant support.
  Trigger: "clickup client wrapper", "clickup SDK patterns", "clickup best practices",
  "clickup typescript client", "clickup API wrapper", "production clickup code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp SDK Patterns

## Overview

ClickUp has no official SDK. Build a typed REST client wrapper around `https://api.clickup.com/api/v2/`. These patterns provide singleton clients, typed responses, error boundaries, and multi-tenant support.

## Typed Client Wrapper

```typescript
// src/clickup/client.ts
const CLICKUP_BASE = 'https://api.clickup.com/api/v2';

interface ClickUpClientConfig {
  token: string;
  timeout?: number;
  onRateLimit?: (waitMs: number) => void;
}

class ClickUpClient {
  private token: string;
  private timeout: number;
  private rateLimitRemaining = 100;
  private rateLimitReset = 0;

  constructor(config: ClickUpClientConfig) {
    this.token = config.token;
    this.timeout = config.timeout ?? 30000;
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${CLICKUP_BASE}${path}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Authorization': this.token,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      // Track rate limit state from response headers
      this.rateLimitRemaining = parseInt(
        response.headers.get('X-RateLimit-Remaining') ?? '100'
      );
      this.rateLimitReset = parseInt(
        response.headers.get('X-RateLimit-Reset') ?? '0'
      ) * 1000;

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new ClickUpApiError(response.status, body.err, body.ECODE);
      }

      return response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  // Convenience methods
  async getUser(): Promise<ClickUpUser> {
    const data = await this.request<{ user: ClickUpUser }>('/user');
    return data.user;
  }

  async getTeams(): Promise<ClickUpTeam[]> {
    const data = await this.request<{ teams: ClickUpTeam[] }>('/team');
    return data.teams;
  }

  async getSpaces(teamId: string): Promise<ClickUpSpace[]> {
    const data = await this.request<{ spaces: ClickUpSpace[] }>(
      `/team/${teamId}/space?archived=false`
    );
    return data.spaces;
  }

  async createTask(listId: string, task: CreateTaskInput): Promise<ClickUpTask> {
    return this.request<ClickUpTask>(`/list/${listId}/task`, {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async getTask(taskId: string): Promise<ClickUpTask> {
    return this.request<ClickUpTask>(`/task/${taskId}`);
  }

  async updateTask(taskId: string, updates: Partial<CreateTaskInput>): Promise<ClickUpTask> {
    return this.request<ClickUpTask>(`/task/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  isRateLimited(): boolean {
    return this.rateLimitRemaining < 5 && Date.now() < this.rateLimitReset;
  }
}
```

## TypeScript Types

```typescript
// src/clickup/types.ts
interface ClickUpUser {
  id: number;
  username: string;
  email: string;
  color: string;
  profilePicture: string | null;
}

interface ClickUpTeam {
  id: string;
  name: string;
  color: string;
  members: Array<{ user: ClickUpUser; role: number }>;
}

interface ClickUpSpace {
  id: string;
  name: string;
  private: boolean;
  statuses: Array<{ status: string; color: string; type: string }>;
  features: Record<string, { enabled: boolean }>;
}

interface ClickUpTask {
  id: string;
  custom_id: string | null;
  name: string;
  description: string;
  status: { status: string; color: string; type: string };
  priority: { id: string; priority: string; color: string } | null;
  date_created: string;
  date_updated: string;
  due_date: string | null;
  assignees: ClickUpUser[];
  tags: Array<{ name: string }>;
  url: string;
  list: { id: string; name: string };
  folder: { id: string; name: string };
  space: { id: string };
  custom_fields: ClickUpCustomFieldValue[];
}

interface CreateTaskInput {
  name: string;
  description?: string;
  markdown_description?: string;
  assignees?: number[];
  priority?: 1 | 2 | 3 | 4 | null;
  status?: string;
  due_date?: number;
  due_date_time?: boolean;
  parent?: string;
  tags?: string[];
  custom_fields?: Array<{ id: string; value: any }>;
}

interface ClickUpCustomFieldValue {
  id: string;
  name: string;
  type: string;
  value: any;
}

class ClickUpApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly err: string,
    public readonly ecode?: string,
  ) {
    super(`ClickUp API ${status}: ${err}${ecode ? ` (${ecode})` : ''}`);
  }

  get isRateLimited(): boolean { return this.status === 429; }
  get isAuthError(): boolean { return this.status === 401; }
  get isNotFound(): boolean { return this.status === 404; }
  get isRetryable(): boolean { return this.status === 429 || this.status >= 500; }
}
```

## Singleton Pattern

```typescript
// src/clickup/index.ts
let defaultClient: ClickUpClient | null = null;

export function getClickUpClient(): ClickUpClient {
  if (!defaultClient) {
    const token = process.env.CLICKUP_API_TOKEN;
    if (!token) throw new Error('CLICKUP_API_TOKEN not set');
    defaultClient = new ClickUpClient({ token });
  }
  return defaultClient;
}
```

## Multi-Tenant Factory

```typescript
const tenantClients = new Map<string, ClickUpClient>();

function getClientForTenant(tenantId: string, token: string): ClickUpClient {
  if (!tenantClients.has(tenantId)) {
    tenantClients.set(tenantId, new ClickUpClient({ token }));
  }
  return tenantClients.get(tenantId)!;
}
```

## Zod Response Validation

```typescript
import { z } from 'zod';

const TaskSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.object({ status: z.string(), color: z.string() }),
  priority: z.object({ priority: z.string() }).nullable(),
  url: z.string().url(),
});

async function getValidatedTask(taskId: string) {
  const raw = await getClickUpClient().getTask(taskId);
  return TaskSchema.parse(raw);
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Typed error class | All API calls | Type-safe error discrimination |
| Singleton | Single-tenant apps | Shared rate limit tracking |
| Factory | Multi-tenant SaaS | Per-tenant isolation |
| Zod validation | Response parsing | Catches API contract changes |

## Resources

- [ClickUp API Reference](https://developer.clickup.com/)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply patterns in `clickup-core-workflow-a` for task management.
