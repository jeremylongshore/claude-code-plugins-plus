---
name: linear-core-workflow-a
description: |
  Issue lifecycle management with Linear: create, update, and transition issues.
  Use when implementing issue CRUD operations, state transitions,
  or building issue management features.
  Trigger with phrases like "linear issue workflow", "linear issue lifecycle",
  "create linear issues", "update linear issue", "linear state transition".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Core Workflow A: Issue Lifecycle

## Overview
Master issue lifecycle management: creating, updating, transitioning, and organizing issues through the Linear SDK and GraphQL API.

## Prerequisites
- Linear SDK installed (`npm install @linear/sdk`)
- API key or OAuth token configured
- Access to target team(s)

## Instructions

### Step 1: Create Issues
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// Get team ID first
const teams = await client.teams();
const team = teams.nodes[0];

// Create a basic issue
const result = await client.createIssue({
  teamId: team.id,
  title: "Implement user authentication",
  description: "Add OAuth 2.0 login flow with Google and GitHub providers",
  priority: 2,  // 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
});

if (result.success) {
  const issue = await result.issue;
  console.log(`Created: ${issue?.identifier} — ${issue?.title}`);
}

// Create with labels, assignee, and project
const labelResult = await client.issueLabels({ filter: { name: { eq: "Bug" } } });
const bugLabel = labelResult.nodes[0];

await client.createIssue({
  teamId: team.id,
  title: "Fix login redirect loop",
  description: "Users get stuck in redirect after SSO callback",
  priority: 1,
  assigneeId: "user-uuid",
  labelIds: [bugLabel.id],
  projectId: "project-uuid",
  estimate: 3,  // Story points
});
```

### Step 2: Update Issues
```typescript
// Update by issue ID
await client.updateIssue("issue-uuid", {
  title: "Updated title",
  priority: 1,
  estimate: 5,
  dueDate: "2025-04-15",
});

// Find issue by identifier (e.g., "ENG-123") then update
const issues = await client.issues({
  filter: { number: { eq: 123 }, team: { key: { eq: "ENG" } } },
});
const issue = issues.nodes[0];
if (issue) {
  await issue.update({ priority: 2, description: "Updated description" });
}
```

### Step 3: State Transitions
Linear issues flow through workflow states with types: `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`.

```typescript
// List workflow states for a team
const states = await team.states();
for (const state of states.nodes) {
  console.log(`${state.name} (${state.type}) — position: ${state.position}`);
}

// Transition an issue to "In Progress"
const inProgressState = states.nodes.find(s => s.name === "In Progress");
if (inProgressState) {
  await client.updateIssue(issue.id, { stateId: inProgressState.id });
}

// Transition to done
const doneState = states.nodes.find(s => s.type === "completed");
if (doneState) {
  await issue.update({ stateId: doneState.id });
}
```

### Step 4: Issue Relationships
```typescript
// Create parent/sub-issue relationship
const parentResult = await client.createIssue({
  teamId: team.id,
  title: "Auth system overhaul",
});
const parent = await parentResult.issue;

await client.createIssue({
  teamId: team.id,
  title: "Implement JWT token refresh",
  parentId: parent!.id,
});

// Create blocking relationship
await client.createIssueRelation({
  issueId: "blocked-issue-id",
  relatedIssueId: "blocking-issue-id",
  type: "blocks",
});
```

### Step 5: Comments and Activity
```typescript
// Add a comment
await client.createComment({
  issueId: issue.id,
  body: "Deployed fix to staging — testing now.\n\n```\nnpm run test:e2e -- --filter auth\n```",
});

// List comments on an issue
const comments = await issue.comments();
for (const comment of comments.nodes) {
  const user = await comment.user;
  console.log(`${user?.name}: ${comment.body.substring(0, 80)}...`);
}
```

## Output
- Issue creation with metadata (labels, assignee, project, priority, estimate)
- Bulk update of issue fields
- Workflow state transitions between triage, backlog, active, done, and canceled
- Parent/sub-issue and blocking relationships
- Threaded comments with Markdown formatting

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Entity not found` | Invalid issue ID or identifier | Verify issue exists: `client.issue(id)` |
| `State not found` | Team workflow mismatch | List states for the correct team: `team.states()` |
| `Validation error` on create | Missing required field or invalid value | `teamId` and `title` are required; check priority range (0-4) |
| `Circular dependency` | Issue blocks itself transitively | Validate relationship graph before creating |

## Examples

### Bulk Create Issues from CSV
```typescript
import { parse } from "csv-parse/sync";
import fs from "fs";

const rows = parse(fs.readFileSync("issues.csv"), { columns: true });
for (const row of rows) {
  const result = await client.createIssue({
    teamId: team.id,
    title: row.title,
    description: row.description,
    priority: parseInt(row.priority) || 3,
  });
  const issue = await result.issue;
  console.log(`Created ${issue?.identifier}`);
}
```

### Find and Close Stale Issues
```typescript
const staleIssues = await client.issues({
  filter: {
    state: { type: { in: ["unstarted", "started"] } },
    updatedAt: { lt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString() },
  },
  first: 50,
});
const canceledState = (await team.states()).nodes.find(s => s.type === "canceled");
for (const issue of staleIssues.nodes) {
  await issue.update({ stateId: canceledState!.id });
  console.log(`Closed stale: ${issue.identifier} (last updated ${issue.updatedAt})`);
}
```

## Resources
- [Linear SDK Getting Started](https://developers.linear.app/docs/sdk/getting-started)
- [Issue Object Reference](https://developers.linear.app/docs/graphql/schema#issue)
- [Workflow States](https://developers.linear.app/docs/graphql/schema#workflowstate)

## Next Steps
Continue to `linear-core-workflow-b` for project and cycle management.
