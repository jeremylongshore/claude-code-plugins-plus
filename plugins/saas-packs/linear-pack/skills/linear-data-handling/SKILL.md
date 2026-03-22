---
name: linear-data-handling
description: |
  Data synchronization, backup, and consistency patterns for Linear.
  Use when implementing data sync, creating backups, exporting data,
  or ensuring data consistency between Linear and local state.
  Trigger: "linear data sync", "backup linear", "linear export",
  "linear data consistency", "sync linear issues".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, backup]

---
# Linear Data Handling

## Overview
Implement reliable data synchronization, backup, and consistency for Linear integrations. Covers full sync, incremental webhook sync, JSON/CSV export, consistency checks, and conflict resolution.

## Prerequisites
- `@linear/sdk` with API key configured
- Database for local storage (any ORM — Drizzle, Prisma, Knex)
- Understanding of eventual consistency

## Instructions

### Step 1: Data Model Schema
```typescript
// src/models/linear-entities.ts
import { z } from "zod";

export const LinearIssueSchema = z.object({
  id: z.string().uuid(),
  identifier: z.string(), // e.g., "ENG-123"
  title: z.string(),
  description: z.string().nullable(),
  priority: z.number().int().min(0).max(4),
  estimate: z.number().nullable(),
  stateId: z.string().uuid(),
  stateName: z.string(),
  stateType: z.string(),
  teamId: z.string().uuid(),
  teamKey: z.string(),
  assigneeId: z.string().uuid().nullable(),
  projectId: z.string().uuid().nullable(),
  cycleId: z.string().uuid().nullable(),
  parentId: z.string().uuid().nullable(),
  dueDate: z.string().nullable(),
  createdAt: z.string(),
  updatedAt: z.string(),
  completedAt: z.string().nullable(),
  canceledAt: z.string().nullable(),
  syncedAt: z.string(),
});

export type LinearIssue = z.infer<typeof LinearIssueSchema>;
```

### Step 2: Full Sync
Paginate through all issues, resolve relations, and upsert locally.

```typescript
import { LinearClient } from "@linear/sdk";

interface SyncStats {
  total: number;
  created: number;
  updated: number;
  deleted: number;
  errors: number;
}

async function fullSync(client: LinearClient, teamKey: string): Promise<SyncStats> {
  const stats: SyncStats = { total: 0, created: 0, updated: 0, deleted: 0, errors: 0 };
  const remoteIds = new Set<string>();

  // Paginate all issues
  let cursor: string | undefined;
  let hasNext = true;

  while (hasNext) {
    const result = await client.client.rawRequest(`
      query FullSync($teamKey: String!, $cursor: String) {
        issues(
          first: 100,
          after: $cursor,
          filter: { team: { key: { eq: $teamKey } } },
          orderBy: updatedAt
        ) {
          nodes {
            id identifier title description priority estimate
            dueDate createdAt updatedAt completedAt canceledAt
            state { id name type }
            team { id key }
            assignee { id }
            project { id }
            cycle { id }
            parent { id }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    `, { teamKey, cursor });

    const issues = result.data.issues;

    for (const issue of issues.nodes) {
      remoteIds.add(issue.id);
      stats.total++;

      try {
        const mapped: LinearIssue = {
          id: issue.id,
          identifier: issue.identifier,
          title: issue.title,
          description: issue.description,
          priority: issue.priority,
          estimate: issue.estimate,
          stateId: issue.state.id,
          stateName: issue.state.name,
          stateType: issue.state.type,
          teamId: issue.team.id,
          teamKey: issue.team.key,
          assigneeId: issue.assignee?.id ?? null,
          projectId: issue.project?.id ?? null,
          cycleId: issue.cycle?.id ?? null,
          parentId: issue.parent?.id ?? null,
          dueDate: issue.dueDate,
          createdAt: issue.createdAt,
          updatedAt: issue.updatedAt,
          completedAt: issue.completedAt,
          canceledAt: issue.canceledAt,
          syncedAt: new Date().toISOString(),
        };

        const existing = await db.issues.findById(issue.id);
        if (existing) {
          await db.issues.update(issue.id, mapped);
          stats.updated++;
        } else {
          await db.issues.insert(mapped);
          stats.created++;
        }
      } catch (error) {
        stats.errors++;
        console.error(`Error syncing ${issue.identifier}:`, error);
      }
    }

    hasNext = issues.pageInfo.hasNextPage;
    cursor = issues.pageInfo.endCursor;

    // Rate limit protection
    if (hasNext) await new Promise(r => setTimeout(r, 100));
  }

  // Soft-delete issues that no longer exist remotely
  const localIds = await db.issues.listIds({ teamKey });
  for (const localId of localIds) {
    if (!remoteIds.has(localId)) {
      await db.issues.softDelete(localId);
      stats.deleted++;
    }
  }

  console.log(`Full sync complete:`, stats);
  return stats;
}
```

### Step 3: Incremental Sync via Webhooks
```typescript
async function processWebhookSync(event: {
  action: "create" | "update" | "remove";
  type: string;
  data: any;
}) {
  if (event.type !== "Issue") return;

  const syncedAt = new Date().toISOString();

  switch (event.action) {
    case "create":
      await db.issues.insert({
        id: event.data.id,
        identifier: event.data.identifier,
        title: event.data.title,
        description: event.data.description,
        priority: event.data.priority,
        estimate: event.data.estimate,
        stateId: event.data.stateId ?? event.data.state?.id,
        stateName: event.data.state?.name ?? "Unknown",
        stateType: event.data.state?.type ?? "unknown",
        teamId: event.data.teamId ?? event.data.team?.id,
        teamKey: event.data.team?.key ?? "",
        assigneeId: event.data.assigneeId ?? null,
        projectId: event.data.projectId ?? null,
        cycleId: event.data.cycleId ?? null,
        parentId: event.data.parentId ?? null,
        dueDate: event.data.dueDate ?? null,
        createdAt: event.data.createdAt,
        updatedAt: event.data.updatedAt,
        completedAt: event.data.completedAt ?? null,
        canceledAt: event.data.canceledAt ?? null,
        syncedAt,
      });
      break;

    case "update":
      await db.issues.update(event.data.id, {
        ...event.data,
        syncedAt,
      });
      break;

    case "remove":
      await db.issues.softDelete(event.data.id);
      break;
  }
}
```

### Step 4: Data Export / Backup
```typescript
async function exportToJson(client: LinearClient, outputDir: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const teams = await client.teams();

  const backup = {
    exportedAt: new Date().toISOString(),
    version: "1.0",
    teams: teams.nodes.map(t => ({ id: t.id, key: t.key, name: t.name })),
    projects: [] as any[],
    issues: [] as any[],
  };

  // Export projects
  const projects = await client.projects();
  backup.projects = projects.nodes.map(p => ({
    id: p.id, name: p.name, state: p.state,
    targetDate: p.targetDate, progress: p.progress,
  }));

  // Export issues with pagination
  for (const team of teams.nodes) {
    let cursor: string | undefined;
    let hasNext = true;
    while (hasNext) {
      const result = await client.issues({
        first: 100,
        after: cursor,
        filter: { team: { id: { eq: team.id } } },
      });
      for (const issue of result.nodes) {
        backup.issues.push({
          id: issue.id,
          identifier: issue.identifier,
          title: issue.title,
          description: issue.description,
          priority: issue.priority,
          estimate: issue.estimate,
          createdAt: issue.createdAt,
          updatedAt: issue.updatedAt,
        });
      }
      hasNext = result.pageInfo.hasNextPage;
      cursor = result.pageInfo.endCursor;
      if (hasNext) await new Promise(r => setTimeout(r, 100));
    }
  }

  const path = `${outputDir}/linear-backup-${timestamp}.json`;
  await fs.writeFile(path, JSON.stringify(backup, null, 2));
  console.log(`Exported ${backup.issues.length} issues to ${path}`);
}
```

### Step 5: Consistency Check
```typescript
async function checkConsistency(client: LinearClient, teamKey: string): Promise<{
  missing: string[];
  stale: string[];
  orphaned: string[];
}> {
  // Sample 50 remote issues
  const remote = await client.issues({
    first: 50,
    filter: { team: { key: { eq: teamKey } } },
    orderBy: "updatedAt",
  });

  const missing: string[] = [];
  const stale: string[] = [];

  for (const issue of remote.nodes) {
    const local = await db.issues.findById(issue.id);
    if (!local) {
      missing.push(issue.identifier);
    } else if (local.updatedAt < issue.updatedAt) {
      stale.push(issue.identifier);
    }
  }

  // Find orphaned local records
  const orphaned: string[] = [];
  const localSample = await db.issues.findRecent(50);
  for (const local of localSample) {
    try {
      await client.issue(local.id);
    } catch {
      orphaned.push(local.identifier);
    }
  }

  const result = { missing, stale, orphaned };
  console.log(`Consistency check: ${missing.length} missing, ${stale.length} stale, ${orphaned.length} orphaned`);

  // Auto-trigger full sync if too many issues
  if (missing.length > 10 || stale.length > 10) {
    console.warn("High inconsistency — triggering full sync");
    await fullSync(client, teamKey);
  }

  return result;
}
```

### Step 6: Conflict Resolution
```typescript
type ConflictStrategy = "remote-wins" | "local-wins" | "merge" | "manual";

interface ConflictResult {
  resolved: boolean;
  strategy: ConflictStrategy;
  winner: "local" | "remote" | "merged";
}

function resolveConflict(
  local: LinearIssue,
  remote: any,
  strategy: ConflictStrategy,
  mergeFields?: string[]
): ConflictResult {
  switch (strategy) {
    case "remote-wins":
      // Remote always wins — standard for most integrations
      db.issues.update(remote.id, { ...remote, syncedAt: new Date().toISOString() });
      return { resolved: true, strategy, winner: "remote" };

    case "local-wins":
      // Keep local, skip remote update
      return { resolved: true, strategy, winner: "local" };

    case "merge":
      // Field-level merge — use remote for specified fields, local for rest
      const merged = { ...local };
      for (const field of mergeFields ?? ["title", "priority", "stateId"]) {
        (merged as any)[field] = remote[field];
      }
      merged.syncedAt = new Date().toISOString();
      db.issues.update(remote.id, merged);
      return { resolved: true, strategy, winner: "merged" };

    case "manual":
      throw new Error(`Conflict on ${local.identifier} requires manual resolution`);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Sync timeout | Too many records | Use smaller page sizes, add delays |
| Conflict detected | Concurrent edits | Apply conflict resolution strategy |
| Stale data | Missed webhook events | Trigger full sync via consistency check |
| Export failed | Rate limit during backup | Add 100ms delay between pagination calls |
| Duplicate entries | Webhook retry without dedup | Deduplicate by `Linear-Delivery` header |

## Resources
- [Linear GraphQL API](https://linear.app/developers/graphql)
- [Linear Pagination](https://linear.app/developers/pagination)
- [Linear Filtering](https://linear.app/developers/filtering)
- [Linear Webhooks](https://linear.app/developers/webhooks)
