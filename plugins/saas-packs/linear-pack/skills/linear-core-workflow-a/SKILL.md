---
name: linear-core-workflow-a
description: |
  Issue lifecycle management with Linear: create, update, transition,
  relate, comment, and organize issues through the SDK and GraphQL API.
  Trigger: "linear issue workflow", "linear issue lifecycle",
  "create linear issues", "update linear issue", "linear state transition",
  "linear sub-issues", "linear comments".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, workflow]

---
# Linear Core Workflow A: Issue Lifecycle

## Overview
Master issue lifecycle management: creating, updating, transitioning states, building parent/sub-issue hierarchies, managing labels, and commenting. Linear issues flow through typed workflow states (`triage` -> `backlog` -> `unstarted` -> `started` -> `completed` | `canceled`), belong to a team, and support priorities 0-4, estimates, due dates, labels, and cycle/project assignment.

## Prerequisites
- `@linear/sdk` installed with API key or OAuth token configured
- Access to target team(s)
- Understanding of your team's workflow states

## Instructions

### Step 1: Create Issues
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// Get team
const teams = await client.teams();
const team = teams.nodes.find(t => t.key === "ENG") ?? teams.nodes[0];

// Basic issue
const result = await client.createIssue({
  teamId: team.id,
  title: "Implement user authentication",
  description: "Add OAuth 2.0 login flow with Google and GitHub providers.",
  priority: 2, // 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
});

if (result.success) {
  const issue = await result.issue;
  console.log(`Created: ${issue?.identifier} — ${issue?.title}`);
  console.log(`URL: ${issue?.url}`);
}

// Issue with full metadata
const labelResult = await client.issueLabels({ filter: { name: { eq: "Bug" } } });
const bugLabel = labelResult.nodes[0];
const states = await team.states();
const todoState = states.nodes.find(s => s.type === "unstarted")!;

await client.createIssue({
  teamId: team.id,
  title: "Fix login redirect loop on Safari",
  description: "Users get stuck in infinite redirect after SSO callback.",
  priority: 1,
  stateId: todoState.id,
  assigneeId: "user-uuid",
  labelIds: bugLabel ? [bugLabel.id] : [],
  estimate: 3,
  dueDate: "2026-04-15",
});
```

### Step 2: Update Issues
```typescript
// Update by issue ID
await client.updateIssue("issue-uuid", {
  title: "Updated title",
  priority: 1,
  estimate: 5,
  dueDate: "2026-04-30",
});

// Find issue by team key + number, then update
const issues = await client.issues({
  filter: { number: { eq: 123 }, team: { key: { eq: "ENG" } } },
});
const issue = issues.nodes[0];
if (issue) {
  await issue.update({
    priority: 2,
    description: "Updated description with more details.",
  });
}

// Add/remove labels
const featureLabel = (await client.issueLabels({
  filter: { name: { eq: "Feature" } },
})).nodes[0];

if (featureLabel) {
  await client.updateIssue(issue.id, {
    labelIds: [...(issue.labelIds ?? []), featureLabel.id],
  });
}
```

### Step 3: State Transitions
```typescript
// List all workflow states for a team
const teamStates = await team.states();
for (const state of teamStates.nodes) {
  console.log(`${state.name} (type: ${state.type}, position: ${state.position})`);
}
// Output example:
// Triage (type: triage, position: 0)
// Backlog (type: backlog, position: 1)
// Todo (type: unstarted, position: 2)
// In Progress (type: started, position: 3)
// In Review (type: started, position: 4)
// Done (type: completed, position: 5)
// Canceled (type: canceled, position: 6)

// Move to "In Progress"
const inProgress = teamStates.nodes.find(s => s.name === "In Progress");
if (inProgress) {
  await client.updateIssue(issue.id, { stateId: inProgress.id });
}

// Complete an issue
const done = teamStates.nodes.find(s => s.type === "completed");
if (done) {
  await issue.update({ stateId: done.id });
}
```

### Step 4: Parent/Sub-Issue Hierarchy
```typescript
// Create parent issue
const parentResult = await client.createIssue({
  teamId: team.id,
  title: "Auth system overhaul",
  description: "Epic: modernize authentication infrastructure.",
});
const parent = await parentResult.issue;

// Create sub-issues under parent
await client.createIssue({
  teamId: team.id,
  title: "Implement JWT token refresh",
  parentId: parent!.id,
  priority: 2,
});

await client.createIssue({
  teamId: team.id,
  title: "Add MFA support",
  parentId: parent!.id,
  priority: 3,
});

// List sub-issues
const children = await parent!.children();
for (const child of children.nodes) {
  console.log(`  Sub: ${child.identifier} — ${child.title}`);
}
```

### Step 5: Issue Relations
```typescript
// Relation types: "blocks", "duplicate", "related"
await client.createIssueRelation({
  issueId: "blocked-issue-id",
  relatedIssueId: "blocking-issue-id",
  type: "blocks",
});

// Mark as duplicate
await client.createIssueRelation({
  issueId: "duplicate-issue-id",
  relatedIssueId: "original-issue-id",
  type: "duplicate",
});

// List relations on an issue
const relations = await issue.relations();
for (const rel of relations.nodes) {
  const related = await rel.relatedIssue;
  console.log(`${rel.type}: ${related?.identifier}`);
}
```

### Step 6: Comments
```typescript
// Add a comment (supports Markdown)
await client.createComment({
  issueId: issue.id,
  body: "Deployed fix to staging.\n\n```bash\nnpm run test:e2e -- --filter auth\n```\n\nAll 47 tests passing.",
});

// List comments on an issue
const comments = await issue.comments();
for (const comment of comments.nodes) {
  const user = await comment.user;
  console.log(`${user?.name}: ${comment.body.substring(0, 80)}...`);
}
```

### Step 7: Attachments
```typescript
// Create a link attachment on an issue
await client.createAttachment({
  issueId: issue.id,
  title: "Figma Design",
  url: "https://figma.com/file/xxx",
  subtitle: "Login page redesign",
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Entity not found` | Invalid issue ID or deleted | Verify with `client.issue(id)` first |
| `State not found` | Wrong team's state ID | List states for correct team: `team.states()` |
| `Validation error` on create | Missing required field | `teamId` + `title` required; priority must be 0-4 |
| `Circular dependency` | Issue blocks itself transitively | Validate relation graph before creating |
| `Forbidden` | No write access to team | Check team membership and API key scope |

## Examples

### Bulk Create from CSV
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
  console.log(`Created: ${issue?.identifier}`);
}
```

### Close Stale Issues
```typescript
const stale = await client.issues({
  filter: {
    state: { type: { in: ["unstarted", "started"] } },
    updatedAt: { lt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString() },
  },
  first: 50,
});

const canceled = (await team.states()).nodes.find(s => s.type === "canceled")!;
for (const issue of stale.nodes) {
  await issue.update({ stateId: canceled.id });
  await client.createComment({
    issueId: issue.id,
    body: "Auto-closed: no activity for 90 days.",
  });
  console.log(`Closed: ${issue.identifier} (last updated ${issue.updatedAt})`);
}
```

## Resources
- [SDK Data Fetching](https://linear.app/developers/sdk-fetching-and-modifying-data)
- [GraphQL Filtering](https://linear.app/developers/filtering)
- [Issue Model Schema](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference/objects/Issue)
