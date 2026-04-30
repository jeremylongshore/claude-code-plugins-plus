---
name: mindtickle-sdk-patterns
description: 'Sdk Patterns for MindTickle.

  Trigger: "mindtickle sdk patterns".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle SDK Patterns

## Overview
MindTickle's REST API serves sales enablement workflows including course management, quiz administration, user progress tracking, SCIM user provisioning, and coaching analytics. A structured SDK client is critical because MindTickle uses compound API keys with org-scoped tokens, returns progress data as nested completion trees with module-level granularity, and enforces strict SCIM schema compliance for user sync. These patterns provide org-aware authentication, typed models for training content hierarchies, progress query builders, and mock factories for sales readiness test scenarios.

## Prerequisites
- Node.js 18+, TypeScript 5+
- `MINDTICKLE_API_KEY` environment variable (generated in Admin > Integrations > API Keys)
- `MINDTICKLE_ORG_ID` for multi-org deployments
- `axios` or `node-fetch` for HTTP transport

## Singleton Client
```typescript
interface MindTickleConfig {
  apiKey: string;
  orgId: string;
  baseUrl?: string;
  timeout?: number;
}

let client: MindTickleClient | null = null;

export function getMindTickleClient(overrides?: Partial<MindTickleConfig>): MindTickleClient {
  if (!client) {
    const config: MindTickleConfig = {
      apiKey: process.env.MINDTICKLE_API_KEY ?? '',
      orgId: process.env.MINDTICKLE_ORG_ID ?? '',
      baseUrl: 'https://api.mindtickle.com/v2',
      timeout: 15_000,
      ...overrides,
    };
    if (!config.apiKey || !config.orgId) throw new Error('MINDTICKLE_API_KEY and MINDTICKLE_ORG_ID are required');
    client = new MindTickleClient(config);
  }
  return client;
}
```

## Error Wrapper
```typescript
interface MindTickleError { statusCode: number; errorType: string; description: string; requestId: string; }

async function safeMindTickle<T>(fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    const parsed: MindTickleError = {
      statusCode: err.response?.status ?? 500,
      errorType: err.response?.data?.error?.type ?? 'INTERNAL_ERROR',
      description: err.response?.data?.error?.description ?? err.message,
      requestId: err.response?.headers?.['x-request-id'] ?? 'unknown',
    };
    if (parsed.statusCode === 429) {
      const retryMs = parseInt(err.response?.headers?.['retry-after-ms'] ?? '3000', 10);
      await new Promise(r => setTimeout(r, retryMs));
      return fn();
    }
    if (parsed.errorType === 'SCIM_CONFLICT') throw new Error(`User already provisioned (req: ${parsed.requestId})`);
    if (parsed.statusCode === 403) throw new Error(`Org ${process.env.MINDTICKLE_ORG_ID} lacks permission: ${parsed.description}`);
    throw new Error(`MindTickle ${parsed.errorType} (${parsed.statusCode}): ${parsed.description} [${parsed.requestId}]`);
  }
}
```

## Request Builder
```typescript
class ProgressQueryBuilder {
  private params: Record<string, string> = {};
  forUser(userId: string) { this.params.user_id = userId; return this; }
  inCourse(courseId: string) { this.params.series_id = courseId; return this; }
  completedAfter(date: string) { this.params.completed_after = date; return this; }
  status(s: 'not_started' | 'in_progress' | 'completed') { this.params.status = s; return this; }
  page(n: number) { this.params.page = String(n); return this; }
  pageSize(n: number) { this.params.page_size = String(Math.min(n, 50)); return this; }
  build(): URLSearchParams { return new URLSearchParams(this.params); }
}
```

## Response Types
```typescript
interface Course { id: string; title: string; moduleCount: number; status: 'draft' | 'published' | 'archived'; createdAt: string; }
interface QuizResult { quizId: string; userId: string; score: number; passingScore: number; passed: boolean; attemptNumber: number; completedAt: string; }
interface UserProgress { userId: string; courseId: string; completedModules: number; totalModules: number; percentComplete: number; lastActivityAt: string; }
interface ScimUser { id: string; userName: string; displayName: string; emails: { value: string; primary: boolean }[]; active: boolean; groups: string[]; }
```

## Middleware Pattern
```typescript
type Middleware = (req: RequestInit, next: () => Promise<Response>) => Promise<Response>;

const orgScopeMiddleware = (orgId: string): Middleware => (req, next) => {
  req.headers = { ...req.headers as Record<string, string>, 'X-MindTickle-Org': orgId, Authorization: `Bearer ${process.env.MINDTICKLE_API_KEY}` };
  return next();
};
const metricsMiddleware: Middleware = async (req, next) => {
  const start = Date.now();
  const res = await next();
  const endpoint = new URL(req.url as string).pathname;
  console.log(`[mindtickle] ${req.method} ${endpoint} ${res.status} ${Date.now() - start}ms`);
  return res;
};
```

## Testing Utilities
```typescript
function mockCourse(overrides?: Partial<Course>): Course {
  return { id: 'series_abc', title: 'Q3 Product Training', moduleCount: 8, status: 'published', createdAt: '2025-07-01T00:00:00Z', ...overrides };
}
function mockProgress(userId: string, courseId: string): UserProgress {
  return { userId, courseId, completedModules: 5, totalModules: 8, percentComplete: 62.5, lastActivityAt: '2025-07-15T14:30:00Z' };
}
function mockScimUser(overrides?: Partial<ScimUser>): ScimUser {
  return { id: 'usr_test_001', userName: 'jsmith@acme.com', displayName: 'Jane Smith', emails: [{ value: 'jsmith@acme.com', primary: true }], active: true, groups: ['sales-east'], ...overrides };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| Retry with header delay | 429 on progress or analytics endpoints | Parse `Retry-After-Ms` header, wait exact duration, retry once |
| SCIM conflict resolution | 409 when provisioning existing user | Fetch existing user by email, update instead of create |
| Org scope validation | 403 on cross-org resource access | Verify `MINDTICKLE_ORG_ID` matches target course owner |
| Completion tree unwrap | Nested module progress with null leaves | Flatten tree, filter nulls, compute rollup percentage |
| Bulk operation chunking | Enrolling 500+ users in a course | Batch into groups of 50, sequential with rate limit pauses |

## Resources
- [MindTickle API Reference](https://www.mindtickle.com/platform/integrations/)

## Next Steps
Apply in `mindtickle-core-workflow-a`.
