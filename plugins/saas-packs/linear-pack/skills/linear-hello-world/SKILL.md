---
name: linear-hello-world
description: |
  Create your first Linear issue and query using the SDK and GraphQL API.
  Use when making initial API calls, testing connection,
  or learning basic Linear CRUD operations.
  Trigger: "linear hello world", "first linear issue",
  "create linear issue", "linear API example", "test linear".
allowed-tools: Read, Write, Edit, Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, graphql, testing]

---
# Linear Hello World

## Overview
Create your first issue, query teams, and explore the Linear data model using the `@linear/sdk`. Linear's API is GraphQL-based -- the SDK wraps it with typed models, lazy-loaded relations, and pagination helpers.

## Prerequisites
- `@linear/sdk` installed (`npm install @linear/sdk`)
- `LINEAR_API_KEY` environment variable set (starts with `lin_api_`)
- Access to at least one Linear team

## Instructions

### Step 1: Connect and Identify
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// Get current authenticated user
const me = await client.viewer;
console.log(`Hello, ${me.name}! (${me.email})`);

// Get your organization
const org = await me.organization;
console.log(`Workspace: ${org.name}`);
```

### Step 2: List Teams
Every issue in Linear belongs to a team. Teams have a short key (e.g., "ENG") used in identifiers like `ENG-123`.

```typescript
const teams = await client.teams();
console.log("Your teams:");
for (const team of teams.nodes) {
  console.log(`  ${team.key} — ${team.name} (${team.id})`);
}
```

### Step 3: Create Your First Issue
```typescript
const team = teams.nodes[0];

const result = await client.createIssue({
  teamId: team.id,
  title: "Hello from Linear SDK!",
  description: "This issue was created using the `@linear/sdk` TypeScript SDK.",
  priority: 3, // 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
});

if (result.success) {
  const issue = await result.issue;
  console.log(`Created: ${issue?.identifier} — ${issue?.title}`);
  console.log(`URL: ${issue?.url}`);
}
```

### Step 4: Query Issues
```typescript
// Get recent issues from a team
const issues = await client.issues({
  filter: {
    team: { key: { eq: team.key } },
    state: { type: { nin: ["completed", "canceled"] } },
  },
  first: 10,
});

console.log(`\nOpen issues in ${team.key}:`);
for (const issue of issues.nodes) {
  const state = await issue.state;
  console.log(`  ${issue.identifier}: ${issue.title} [${state?.name}]`);
}
```

### Step 5: Explore Workflow States
Each team has customizable workflow states organized by type: `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`.

```typescript
const states = await team.states();
console.log(`\nWorkflow states for ${team.key}:`);
for (const state of states.nodes) {
  console.log(`  ${state.name} (type: ${state.type}, position: ${state.position})`);
}
```

### Step 6: Fetch a Single Issue by Identifier
```typescript
// Search for a specific issue by its human-readable identifier
const searchResults = await client.issueSearch("ENG-1");
const found = searchResults.nodes[0];
if (found) {
  console.log(`\nFound: ${found.identifier}`);
  console.log(`  Title: ${found.title}`);
  console.log(`  Priority: ${found.priority}`);
  console.log(`  Created: ${found.createdAt}`);
  const assignee = await found.assignee;
  console.log(`  Assignee: ${assignee?.name ?? "Unassigned"}`);
}
```

### Step 7: Raw GraphQL Query
The SDK exposes the underlying GraphQL client for custom queries.

```typescript
const response = await client.client.rawRequest(`
  query TeamDashboard($teamKey: String!) {
    teams(filter: { key: { eq: $teamKey } }) {
      nodes {
        name
        key
        issues(first: 5, orderBy: updatedAt) {
          nodes {
            identifier
            title
            priority
            state { name type }
            assignee { name }
          }
        }
      }
    }
  }
`, { teamKey: "ENG" });

console.log(JSON.stringify(response.data, null, 2));
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication required` | Invalid API key | Regenerate at Settings > Account > API |
| `Entity not found` | Invalid ID or no access | Use `client.teams()` first to get valid IDs |
| `Validation error` | Missing required field | `teamId` and `title` are required for `createIssue` |
| `Cannot read properties of null` | Accessing nullable relation | Use optional chaining: `(await issue.assignee)?.name` |

## Examples

### Complete Hello World Script
```typescript
import { LinearClient } from "@linear/sdk";

async function main() {
  const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

  const me = await client.viewer;
  console.log(`Connected as ${me.name}\n`);

  const teams = await client.teams();
  const team = teams.nodes[0];

  // Create issue
  const result = await client.createIssue({
    teamId: team.id,
    title: "Hello from Linear SDK!",
    description: "Testing the API integration.",
    priority: 3,
  });

  if (result.success) {
    const issue = await result.issue;
    console.log(`Created: ${issue?.identifier} — ${issue?.url}`);

    // Read it back
    const fetched = await client.issue(issue!.id);
    console.log(`Verified: ${fetched.title}`);

    // Clean up
    await fetched.delete();
    console.log("Deleted test issue.");
  }
}

main().catch(console.error);
```

## Resources
- [Linear SDK Documentation](https://linear.app/developers/sdk)
- [SDK Data Fetching](https://linear.app/developers/sdk-fetching-and-modifying-data)
- [GraphQL Schema Explorer](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference)
