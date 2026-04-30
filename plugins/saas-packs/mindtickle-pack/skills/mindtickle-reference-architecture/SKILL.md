---
name: mindtickle-reference-architecture
description: 'Reference Architecture for MindTickle.

  Trigger: "mindtickle reference architecture".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Reference Architecture

## Overview
Design a multi-tenant integration layer for the MindTickle sales enablement platform. Strict tenant data isolation is the primary driver, enforced at the database, cache, and queue levels so training data, quiz scores, and readiness analytics never cross organizational boundaries.

## Instructions
1. Provision the prerequisites below with Row-Level Security enabled in PostgreSQL.
2. Configure SCIM 2.0 webhook endpoints to receive HR system user events.
3. Deploy the enablement service with tenant-scoped database connections.
4. Start the SCIM consumer and analytics aggregator as separate worker processes.
5. Validate tenant isolation by running cross-tenant query tests against RLS policies.

## Prerequisites
- Node.js 18+, TypeScript 5, PostgreSQL 15 with RLS, Redis 7, RabbitMQ or SQS
- MindTickle API key with `users:read`, `courses:read`, `analytics:read` scopes
- SCIM 2.0 endpoint credentials for user provisioning

## Architecture Diagram
```
HR System --> SCIM Webhook Ingester --> User Sync Service --> MindTickle API
                                             |
Client --> API Gateway --> EnablementService --+--> Analytics Aggregator
                                |
                         Tenant-scoped PostgreSQL (RLS)
```

## Service Layer
```typescript
class EnablementService {
  constructor(
    private api: MindTickleApiClient,
    private db: TenantScopedStore,
    private events: EventPublisher
  ) {}

  async syncCourseProgress(tenantId: string, userId: string): Promise<Progress> {
    const courses = await this.api.getUserCourses(userId);
    const progress = courses.map(c => ({
      courseId: c.id, status: c.status, score: c.quizScore, completedAt: c.completedAt,
    }));
    await this.db.upsertProgress(tenantId, userId, progress);
    await this.events.publish('progress.synced', { tenantId, userId });
    return { userId, courses: progress };
  }

  async processQuizResult(tenantId: string, result: QuizSubmission): Promise<void> {
    await this.db.recordQuizResult(tenantId, result);
    await this.events.publish('quiz.completed', { tenantId, ...result });
  }
}
```

## Caching Strategy
```typescript
class TenantCache {
  constructor(private redis: RedisClient) {}

  private key(tenantId: string, resource: string): string {
    return `tenant:${tenantId}:${resource}`;
  }

  async getUserRoster(tenantId: string): Promise<User[] | null> {
    const raw = await this.redis.get(this.key(tenantId, 'roster'));
    return raw ? JSON.parse(raw) : null;
  }

  async setUserRoster(tenantId: string, users: User[]): Promise<void> {
    await this.redis.setEx(this.key(tenantId, 'roster'), 600, JSON.stringify(users));
  }

  async invalidateTenant(tenantId: string): Promise<void> {
    const keys = await this.redis.keys(`tenant:${tenantId}:*`);
    if (keys.length) await this.redis.del(keys);
  }
}
// TTLs: roster 10 min, course catalog 30 min, quiz results not cached
```

## Event Pipeline
```typescript
class ScimWebhookConsumer {
  constructor(private queue: MessageQueue, private db: TenantScopedStore) {}

  async handleScimEvent(payload: ScimPayload): Promise<void> {
    const tenantId = payload.tenantId;
    if (payload.operation === 'CREATE') {
      await this.db.provisionUser(tenantId, payload.user);
    } else if (payload.operation === 'DELETE') {
      await this.db.deactivateUser(tenantId, payload.user.id);
    }
    await this.queue.publish(`tenant.${tenantId}.user_changed`, payload);
  }
}

class AnalyticsAggregator {
  async aggregateTeamReadiness(tenantId: string): Promise<ReadinessReport> {
    const scores = await this.db.getQuizScores(tenantId);
    const completion = await this.db.getCourseCompletion(tenantId);
    return { tenantId, avgScore: mean(scores), completionRate: ratio(completion) };
  }
}
```

## Data Model
```typescript
interface User {
  id: string; tenantId: string; email: string;
  role: 'rep' | 'manager' | 'admin';
  scimExternalId: string; active: boolean;
}
interface CourseProgress {
  userId: string; courseId: string;
  status: 'not_started' | 'in_progress' | 'completed';
  score: number | null; completedAt: Date | null;
}
interface QuizSubmission {
  userId: string; courseId: string; quizId: string;
  answers: { questionId: string; selected: string; correct: boolean }[];
  score: number; submittedAt: Date;
}
interface ReadinessReport {
  tenantId: string; avgScore: number; completionRate: number;
}
```

## Output
Running this architecture produces tenant-isolated user rosters synced via SCIM, a course progress tracker with quiz scoring, and aggregated team readiness reports partitioned by organization.

## Scaling Considerations
- Enforce Row-Level Security in PostgreSQL so every query is tenant-scoped by default
- Partition Redis keyspace by tenant prefix to enable per-tenant eviction policies
- Route SCIM webhooks to tenant-specific queue channels to prevent noisy-neighbor stalls
- Use connection pooling per tenant to respect MindTickle per-org rate limits (60 req/min)

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| MindTickle API | 429 rate limit | Per-tenant backoff, queue surplus for next window |
| SCIM Ingester | Malformed payload | Reject with 400, log to DLQ for manual review |
| Tenant DB | RLS policy violation | Block query, alert on cross-tenant access attempt |
| Analytics Aggregator | Stale data | Mark report provisional, schedule re-aggregation |
| Event Queue | Tenant channel backup | Spill to overflow queue, process FIFO on recovery |

## Examples
```bash
# Sync course progress for a specific user in a tenant
curl http://localhost:3000/api/tenants/acme/users/u123/sync-progress
# Trigger a team readiness report aggregation
curl -X POST http://localhost:3000/api/tenants/acme/readiness/aggregate
```

## Resources
- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-deploy-integration`.
