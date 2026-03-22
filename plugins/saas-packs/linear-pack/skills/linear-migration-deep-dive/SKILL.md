---
name: linear-migration-deep-dive
description: |
  Migrate from Jira, Asana, GitHub Issues, or other tools to Linear.
  Use when planning a migration, executing data transfer,
  or mapping workflows between issue tracking tools.
  Trigger: "migrate to linear", "jira to linear", "asana to linear",
  "import to linear", "linear migration", "github issues to linear".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, migration, workflow]

---
# Linear Migration Deep Dive

## Overview
Comprehensive guide for migrating from Jira, Asana, or GitHub Issues to Linear. Covers assessment, workflow mapping, data export, transformation, batch import with hierarchy support, and post-migration validation. Linear also has a built-in importer (Settings > Import) for Jira, Asana, GitHub, and CSV.

## Prerequisites
- Admin access to source system (Jira/Asana/GitHub)
- Linear workspace with admin access
- API keys for both source and Linear
- Migration timeline and rollback plan

## Instructions

### Step 1: Migration Assessment Checklist
```
Data Volume
[ ] Total issues/tasks: ___
[ ] Projects/boards: ___
[ ] Users to map: ___
[ ] Attachments: ___
[ ] Custom fields: ___
[ ] Comments: ___

Workflow Analysis
[ ] Source statuses documented
[ ] Status-to-state mapping defined
[ ] Priority mapping defined
[ ] Issue type-to-label mapping defined
[ ] Automations to recreate: ___

Timeline
[ ] Migration window: ___
[ ] Parallel run period: ___
[ ] Cutover date: ___
[ ] Rollback deadline: ___
```

### Step 2: Workflow Mapping

**Jira -> Linear:**
| Jira Status | Linear State (type) |
|-------------|-------------------|
| To Do | Todo (unstarted) |
| In Progress | In Progress (started) |
| In Review | In Review (started) |
| Blocked | In Progress (started) + "Blocked" label |
| Done | Done (completed) |
| Won't Do | Canceled (canceled) |

| Jira Priority | Linear Priority |
|---------------|----------------|
| Highest/Blocker | 1 (Urgent) |
| High | 2 (High) |
| Medium | 3 (Medium) |
| Low/Lowest | 4 (Low) |

| Jira Issue Type | Linear Label |
|-----------------|-------------|
| Bug | Bug |
| Story | Feature |
| Task | Task |
| Epic | (becomes Project or parent issue) |

**Asana -> Linear:**
| Asana Section | Linear State |
|---------------|-------------|
| Backlog | Backlog (backlog) |
| To Do | Todo (unstarted) |
| In Progress | In Progress (started) |
| Review | In Review (started) |
| Done | Done (completed) |

### Step 3: Export from Source System

**Jira Export:**
```typescript
// src/migration/jira-exporter.ts
interface JiraIssue {
  key: string;
  summary: string;
  description: string;
  status: string;
  priority: string;
  issuetype: string;
  assignee?: string;
  labels: string[];
  storyPoints?: number;
  parent?: string;
  subtasks: string[];
}

async function exportJiraProject(
  baseUrl: string,
  projectKey: string,
  authToken: string
): Promise<JiraIssue[]> {
  const issues: JiraIssue[] = [];
  let startAt = 0;
  const maxResults = 100;

  while (true) {
    const jql = `project = ${projectKey} ORDER BY created ASC`;
    const response = await fetch(
      `${baseUrl}/rest/api/3/search?jql=${encodeURIComponent(jql)}&startAt=${startAt}&maxResults=${maxResults}&fields=summary,description,status,priority,issuetype,assignee,labels,customfield_10016,parent,subtasks`,
      { headers: { Authorization: `Basic ${authToken}`, Accept: "application/json" } }
    );

    const data = await response.json();
    for (const issue of data.issues) {
      issues.push({
        key: issue.key,
        summary: issue.fields.summary,
        description: issue.fields.description?.content
          ? convertAtlassianDocToMarkdown(issue.fields.description)
          : issue.fields.description ?? "",
        status: issue.fields.status.name,
        priority: issue.fields.priority?.name ?? "Medium",
        issuetype: issue.fields.issuetype.name,
        assignee: issue.fields.assignee?.emailAddress,
        labels: issue.fields.labels ?? [],
        storyPoints: issue.fields.customfield_10016,
        parent: issue.fields.parent?.key,
        subtasks: issue.fields.subtasks?.map((s: any) => s.key) ?? [],
      });
    }

    startAt += maxResults;
    if (startAt >= data.total) break;
  }

  console.log(`Exported ${issues.length} issues from Jira ${projectKey}`);
  return issues;
}
```

**Jira Markup -> Markdown Converter:**
```typescript
function convertJiraToMarkdown(text: string): string {
  if (!text) return "";
  return text
    .replace(/h([1-6])\.\s/g, (_, level) => "#".repeat(parseInt(level)) + " ")
    .replace(/\*([^*]+)\*/g, "**$1**")
    .replace(/_([^_]+)_/g, "*$1*")
    .replace(/\{code(?::([^}]*))?\}([\s\S]*?)\{code\}/g, "```$1\n$2\n```")
    .replace(/\{noformat\}([\s\S]*?)\{noformat\}/g, "```\n$1\n```")
    .replace(/^\*\s/gm, "- ")
    .replace(/^#\s/gm, "1. ")
    .replace(/\[([^|]+)\|([^\]]+)\]/g, "[$1]($2)");
}
```

### Step 4: Transform to Linear Format
```typescript
interface LinearImportIssue {
  title: string;
  description: string;
  priority: number;
  stateId: string;
  assigneeId?: string;
  labelIds: string[];
  estimate?: number;
  parentId?: string;
  sourceId: string; // Original ID for tracking
}

async function transformJiraIssue(
  jiraIssue: JiraIssue,
  stateMap: Map<string, string>,
  userMap: Map<string, string>,
  labelMap: Map<string, string>
): Promise<LinearImportIssue> {
  // Priority mapping
  const priorityMap: Record<string, number> = {
    Highest: 1, Blocker: 1,
    High: 2,
    Medium: 3,
    Low: 4, Lowest: 4,
  };

  // Map labels
  const labelIds: string[] = [];
  // Issue type becomes a label
  const typeLabel = labelMap.get(jiraIssue.issuetype);
  if (typeLabel) labelIds.push(typeLabel);
  // Original Jira labels
  for (const label of jiraIssue.labels) {
    const mapped = labelMap.get(label);
    if (mapped) labelIds.push(mapped);
  }

  return {
    title: jiraIssue.summary,
    description: convertJiraToMarkdown(jiraIssue.description),
    priority: priorityMap[jiraIssue.priority] ?? 3,
    stateId: stateMap.get(jiraIssue.status) ?? stateMap.get("Todo")!,
    assigneeId: jiraIssue.assignee ? userMap.get(jiraIssue.assignee) : undefined,
    labelIds,
    estimate: jiraIssue.storyPoints ?? undefined,
    sourceId: jiraIssue.key,
  };
}
```

### Step 5: Import to Linear
```typescript
import { LinearClient } from "@linear/sdk";

async function importToLinear(
  client: LinearClient,
  teamId: string,
  issues: JiraIssue[],
  stateMap: Map<string, string>,
  userMap: Map<string, string>,
  labelMap: Map<string, string>
): Promise<{ created: number; errors: number; idMap: Map<string, string> }> {
  const idMap = new Map<string, string>(); // sourceId -> linearId
  let created = 0;
  let errors = 0;

  // Sort: parents first, then children
  const sorted = [...issues].sort((a, b) => {
    if (a.subtasks.length > 0 && !a.parent) return -1; // Parents first
    if (b.subtasks.length > 0 && !b.parent) return 1;
    return 0;
  });

  for (const jiraIssue of sorted) {
    try {
      const transformed = await transformJiraIssue(jiraIssue, stateMap, userMap, labelMap);

      // Set parent if it was already imported
      if (jiraIssue.parent && idMap.has(jiraIssue.parent)) {
        transformed.parentId = idMap.get(jiraIssue.parent);
      }

      const result = await client.createIssue({
        teamId,
        title: transformed.title,
        description: `${transformed.description}\n\n---\n*Migrated from ${jiraIssue.key}*`,
        priority: transformed.priority,
        stateId: transformed.stateId,
        assigneeId: transformed.assigneeId,
        labelIds: transformed.labelIds,
        estimate: transformed.estimate,
        parentId: transformed.parentId,
      });

      if (result.success) {
        const issue = await result.issue;
        idMap.set(jiraIssue.key, issue!.id);
        created++;
        if (created % 25 === 0) console.log(`Imported ${created}/${sorted.length}`);
      }

      // Rate limit: 100ms between requests
      await new Promise(r => setTimeout(r, 100));
    } catch (error: any) {
      console.error(`Failed to import ${jiraIssue.key}: ${error.message}`);
      errors++;
    }
  }

  console.log(`Import complete: ${created} created, ${errors} errors`);
  return { created, errors, idMap };
}
```

### Step 6: Post-Migration Validation
```typescript
async function validateMigration(
  client: LinearClient,
  teamId: string,
  sourceIssues: JiraIssue[],
  idMap: Map<string, string>
): Promise<{ valid: boolean; issues: string[] }> {
  const problems: string[] = [];

  // Check all issues were imported
  if (idMap.size < sourceIssues.length) {
    problems.push(`Missing: ${sourceIssues.length - idMap.size} issues not imported`);
  }

  // Sample validation: check 50 random issues
  const sample = sourceIssues.slice(0, 50);
  for (const source of sample) {
    const linearId = idMap.get(source.key);
    if (!linearId) {
      problems.push(`${source.key}: not imported`);
      continue;
    }

    try {
      const issue = await client.issue(linearId);
      if (issue.title !== source.summary) {
        problems.push(`${source.key}: title mismatch`);
      }
    } catch {
      problems.push(`${source.key}: not found in Linear (${linearId})`);
    }

    await new Promise(r => setTimeout(r, 50));
  }

  return { valid: problems.length === 0, issues: problems };
}
```

## Post-Migration Checklist
```
[ ] All issues imported and validated
[ ] Parent/child relationships correct
[ ] Labels and priorities mapped correctly
[ ] User assignments transferred
[ ] Integrations reconfigured (GitHub, Slack)
[ ] Team workflows customized in Linear
[ ] Team trained on Linear
[ ] Source system set to read-only
[ ] Parallel run period started (2 weeks recommended)
[ ] Archive source system after parallel run
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| User not found | Unmapped email | Add to userMap |
| Rate limited | Too fast import | Increase delay to 200ms |
| State not found | Unmapped status | Update stateMap |
| Parent not found | Import order wrong | Sort parents before children |
| Markup broken | Incomplete conversion | Improve markdown converter |

## Resources
- [Linear Import (Built-in)](https://linear.app/docs/import-issues)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Asana API](https://developers.asana.com/reference)
- [Linear GraphQL API](https://linear.app/developers/graphql)
