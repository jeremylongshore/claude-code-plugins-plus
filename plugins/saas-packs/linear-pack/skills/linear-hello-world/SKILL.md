---
name: linear-hello-world
description: |
  Create your first Linear issue and query using the GraphQL API.
  Use when making initial API calls, testing Linear connection,
  or learning basic Linear operations.
  Trigger with phrases like "linear hello world", "first linear issue",
  "create linear issue", "linear API example", "test linear connection".
allowed-tools: Read, Write, Edit, Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Hello World

## Overview
Create your first issue and execute basic queries with the Linear API.

## Prerequisites
- Linear SDK installed (`@linear/sdk`)
- Valid API key configured
- Access to at least one Linear team

## Instructions

### Step 1: Query Your Teams
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });

// Get all teams you have access to
const teams = await client.teams();
console.log("Your teams:");
teams.nodes.forEach(team => {
  console.log(`  - ${team.name} (${team.key})`);
});
```

### Step 2: Create Your First Issue
```typescript
// Get the first team
const team = teams.nodes[0];

// Create an issue
const issueCreate = await client.createIssue({
  teamId: team.id,
  title: "My first Linear issue from the API",
  description: "This issue was created using the Linear SDK!",
});

if (issueCreate.success) {
  const issue = await issueCreate.issue;
  console.log(`Created issue: ${issue?.identifier} - ${issue?.title}`);
  console.log(`URL: ${issue?.url}`);
}
```

### Step 3: Query Issues
```typescript
// Get recent issues from your team
const issues = await client.issues({
  filter: {
    team: { key: { eq: team.key } },
  },
  first: 10,
});

console.log("Recent issues:");
issues.nodes.forEach(issue => {
  console.log(`  ${issue.identifier}: ${issue.title} [${issue.state?.name}]`);
});
```

## Output
- List of teams you have access to
- Created issue with identifier and URL
- Query results showing recent issues

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Team not found` | Invalid team ID or no access | Use `client.teams()` to list accessible teams |
| `Validation error` | Missing required fields | Ensure title and teamId are provided |
| `Permission denied` | Insufficient permissions | Check API key scope in Linear settings |
| `Rate limited` | Too many requests | Add delays between requests |

## Examples

### Complete Hello World Script
```typescript
import { LinearClient } from "@linear/sdk";

async function helloLinear() {
  const client = new LinearClient({
    apiKey: process.env.LINEAR_API_KEY
  });

  // 1. Get current user
  const viewer = await client.viewer;
  console.log(`Hello, ${viewer.name}!`);

  // 2. List teams
  const teams = await client.teams();
  const team = teams.nodes[0];
  console.log(`Using team: ${team.name}`);

  // 3. Create issue
  const result = await client.createIssue({
    teamId: team.id,
    title: "Hello from Linear SDK!",
    description: "Testing the Linear API integration.",
    priority: 2, // Medium priority
  });

  if (result.success) {
    const issue = await result.issue;
    console.log(`Created: ${issue?.identifier}`);
  }

  // 4. Query issues
  const issues = await client.issues({ first: 5 });
  console.log(`\nYour latest ${issues.nodes.length} issues:`);
  issues.nodes.forEach(i => console.log(`  - ${i.identifier}: ${i.title}`));
}

helloLinear().catch(console.error);
```

### Using GraphQL Directly
```typescript
const query = `
  query Me {
    viewer {
      id
      name
      email
    }
  }
`;

const response = await fetch("https://api.linear.app/graphql", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": process.env.LINEAR_API_KEY,
  },
  body: JSON.stringify({ query }),
});

const data = await response.json();
console.log(data);
```

## Resources
- [Linear SDK Getting Started](https://developers.linear.app/docs/sdk/getting-started)
- [GraphQL API Reference](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Issue Object Reference](https://developers.linear.app/docs/graphql/schema#issue)

## Next Steps
After creating your first issue, proceed to `linear-sdk-patterns` for best practices.