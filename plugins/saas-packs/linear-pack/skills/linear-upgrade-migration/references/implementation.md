# Linear Upgrade Migration - Implementation Details

## Migration Patterns

### Pattern A: Renamed Fields
```typescript
// Before (deprecated)
const issue = await client.issue("ABC-123");
console.log(issue.state); // Old field name

// After (new version)
const issue = await client.issue("ABC-123");
const state = await issue.state; // Now returns Promise
console.log(state?.name);
```

### Pattern B: Changed Return Types
```typescript
// Before: Direct object return
const teams = await client.teams();
teams.forEach(team => console.log(team.name));

// After: Paginated connection
const teams = await client.teams();
teams.nodes.forEach(team => console.log(team.name));
```

### Pattern C: New Required Parameters
```typescript
// Before
await client.createIssue({ title: "Issue" });

// After: teamId is required
await client.createIssue({ title: "Issue", teamId: team.id });
```

### Pattern D: Removed Methods
```typescript
if (typeof client.deprecatedMethod === "function") {
  await client.deprecatedMethod();
} else {
  await client.newMethod();
}
```

## Compatibility Layer

```typescript
// lib/linear-compat.ts
import { LinearClient, Issue } from "@linear/sdk";

export class LinearCompatClient {
  private client: LinearClient;

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  async getIssue(identifier: string): Promise<{
    id: string;
    title: string;
    stateName: string;
  }> {
    const issue = await this.client.issue(identifier);
    const state = await issue.state;
    return {
      id: issue.id,
      title: issue.title,
      stateName: state?.name ?? "Unknown",
    };
  }
}
```

## SDK Version Changes

### SDK 1.x to 2.x
```typescript
// 1.x: CommonJS
const { LinearClient } = require("@linear/sdk");

// 2.x: ESM
import { LinearClient } from "@linear/sdk";

// Update package.json: { "type": "module" }
```

### SDK 2.x to 3.x
```typescript
// 2.x: Loose types
const issue: any = await client.issue("ABC-123");

// 3.x: Strict types - must handle nullable fields
const issue: Issue = await client.issue("ABC-123");
const state = await issue.state;
if (state) {
  console.log(state.name);
}
```

## Gradual Rollout Pattern

```typescript
const USE_NEW_SDK = process.env.LINEAR_SDK_V2 === "true";

async function getIssues() {
  if (USE_NEW_SDK) {
    return newGetIssues();
  } else {
    return legacyGetIssues();
  }
}
```

## Rollback Procedure

```bash
git checkout main
npm install @linear/sdk@PREVIOUS_VERSION
npm run test
git commit -am "Rollback Linear SDK to PREVIOUS_VERSION"
```
