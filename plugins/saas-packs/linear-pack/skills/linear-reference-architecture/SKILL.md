---
name: linear-reference-architecture
description: |
  Production-grade Linear integration architecture patterns.
  Use when designing system architecture, choosing integration patterns,
  or reviewing architectural decisions for Linear integrations.
  Trigger: "linear architecture", "linear system design",
  "linear integration patterns", "linear best practices architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, linear-reference]

---
# Linear Reference Architecture

## Overview
Production-grade architectural patterns for Linear integrations. Choose the right pattern based on team size, complexity, and real-time requirements.

## Architecture Decision Matrix

| Pattern | Best For | Complexity | Rate Budget | Example |
|---------|----------|------------|-------------|---------|
| Simple | Single app, small team | Low | < 500 req/hr | Internal dashboard |
| Service-Oriented | Multiple apps, shared state | Medium | 500-2,000 req/hr | Platform with Linear sync |
| Event-Driven | Real-time needs, many consumers | High | < 500 req/hr + webhooks | Multi-service notification system |
| CQRS | Audit trails, complex queries | Very High | Minimal API calls | Compliance-grade tracking |

## Architecture 1: Simple Integration
Direct SDK calls from your application. Best for scripts, internal tools, and prototypes.

```typescript
// src/linear.ts — single module, shared client
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// Direct SDK calls from any part of your app
export async function getOpenIssues(teamKey: string) {
  return client.issues({
    first: 50,
    filter: {
      team: { key: { eq: teamKey } },
      state: { type: { nin: ["completed", "canceled"] } },
    },
    orderBy: "priority",
  });
}

export async function createBugReport(teamId: string, title: string, description: string) {
  const labels = await client.issueLabels({ filter: { name: { eq: "Bug" } } });
  return client.createIssue({
    teamId,
    title,
    description,
    priority: 2,
    labelIds: labels.nodes.length ? [labels.nodes[0].id] : [],
  });
}
```

## Architecture 2: Service-Oriented with Gateway
Centralized Linear access through a gateway service with caching and rate limiting.

```typescript
// src/linear-gateway.ts
import { LinearClient } from "@linear/sdk";

class LinearGateway {
  private client: LinearClient;
  private cache = new Map<string, { data: any; expiresAt: number }>();
  private requestQueue: Array<{ fn: () => Promise<any>; resolve: Function; reject: Function }> = [];
  private processing = false;

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  // Cached reads
  async getTeams() {
    return this.cachedQuery("teams", () => this.client.teams().then(r => r.nodes), 600);
  }

  async getStates(teamId: string) {
    return this.cachedQuery(`states:${teamId}`, async () => {
      const team = await this.client.team(teamId);
      return (await team.states()).nodes;
    }, 1800);
  }

  // Rate-limited writes
  async createIssue(input: any) {
    return this.enqueue(() => this.client.createIssue(input));
  }

  async updateIssue(id: string, input: any) {
    return this.enqueue(() => this.client.updateIssue(id, input));
  }

  // Custom queries through the gateway
  async rawQuery(query: string, variables?: any) {
    return this.enqueue(() => this.client.client.rawRequest(query, variables));
  }

  // Cache invalidation (called from webhook handler)
  invalidate(pattern: string) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(pattern)) this.cache.delete(key);
    }
  }

  private async cachedQuery<T>(key: string, fn: () => Promise<T>, ttlSec: number): Promise<T> {
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiresAt) return cached.data;
    const data = await this.enqueue(fn);
    this.cache.set(key, { data, expiresAt: Date.now() + ttlSec * 1000 });
    return data;
  }

  private async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({ fn, resolve, reject });
      if (!this.processing) this.processQueue();
    });
  }

  private async processQueue() {
    this.processing = true;
    while (this.requestQueue.length > 0) {
      const { fn, resolve, reject } = this.requestQueue.shift()!;
      try { resolve(await fn()); } catch (e) { reject(e); }
      if (this.requestQueue.length > 0) {
        await new Promise(r => setTimeout(r, 100)); // 10 req/sec max
      }
    }
    this.processing = false;
  }
}

export const gateway = new LinearGateway(process.env.LINEAR_API_KEY!);
```

## Architecture 3: Event-Driven
Webhook-centric architecture. Minimal API calls, real-time processing.

```typescript
// src/event-processor.ts
import express from "express";
import crypto from "crypto";
import { EventEmitter } from "events";

// Internal event bus
const bus = new EventEmitter();

// Webhook ingester
const app = express();
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const sig = req.headers["linear-signature"] as string;
  const body = req.body.toString();
  const expected = crypto.createHmac("sha256", process.env.LINEAR_WEBHOOK_SECRET!)
    .update(body).digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) {
    return res.status(401).end();
  }

  const event = JSON.parse(body);
  res.json({ ok: true });

  // Emit to internal consumers
  bus.emit(`${event.type}.${event.action}`, event);
  bus.emit(event.type, event);
  bus.emit("*", event);
});

// Consumer: Slack notifications
bus.on("Issue.update", async (event) => {
  if (event.updatedFrom?.stateId && event.data.state?.type === "completed") {
    await notifySlack(`Done: ${event.data.identifier} ${event.data.title}`);
  }
});

// Consumer: Database sync
bus.on("Issue", async (event) => {
  if (event.action === "create") await db.issues.insert(event.data);
  if (event.action === "update") await db.issues.update(event.data.id, event.data);
  if (event.action === "remove") await db.issues.softDelete(event.data.id);
});

// Consumer: Cache invalidation
bus.on("*", (event) => {
  gateway.invalidate(event.type.toLowerCase());
});
```

## Architecture 4: CQRS with Local State
Separate read and write paths. Full local state for complex queries, API for writes.

```typescript
// Write side: mutations go through Linear API
async function createIssue(input: any) {
  const result = await gateway.createIssue(input);
  // Local state updated via webhook, not here
  return result;
}

// Read side: queries against local database (no API calls)
async function getSprintVelocity(teamKey: string, sprints: number) {
  return db.query(`
    SELECT c.name, SUM(i.estimate) as velocity
    FROM cycles c
    JOIN issues i ON i.cycle_id = c.id AND i.state_type = 'completed'
    WHERE c.team_key = ? AND c.completed_at IS NOT NULL
    ORDER BY c.completed_at DESC
    LIMIT ?
  `, [teamKey, sprints]);
}

// Sync: webhook events keep local state fresh
// Full sync: daily consistency check (see linear-data-handling)
```

## Project Structure
```
src/
  linear/
    gateway.ts          # Rate-limited, cached API access
    webhook-handler.ts  # Signature verification + routing
    event-bus.ts        # Internal event distribution
    cache.ts            # TTL cache with invalidation
  services/
    issue-service.ts    # Business logic
    sync-service.ts     # Data synchronization
  config/
    linear.ts           # Environment config + validation
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limit exceeded | Too many direct API calls | Route all calls through gateway |
| Stale cache | TTL too long, missed webhook | Webhook invalidation + periodic full sync |
| Event loss | Webhook delivery failure | Idempotent handlers + consistency checks |
| Schema drift | SDK version mismatch | Pin version, test upgrades in staging |

## Resources
- [Linear API Best Practices](https://linear.app/developers/graphql)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
