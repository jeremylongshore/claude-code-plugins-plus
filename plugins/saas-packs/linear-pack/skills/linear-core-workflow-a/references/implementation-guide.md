# Linear Core Workflow A: Issue Lifecycle - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Create Issues
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });

async function createIssue(options: {
  teamKey: string;
  title: string;
  description?: string;
  priority?: 0 | 1 | 2 | 3 | 4; // 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
  estimate?: number;
  labelIds?: string[];
  assigneeId?: string;
}) {
  const teams = await client.teams({ filter: { key: { eq: options.teamKey } } });
  const team = teams.nodes[0];

  if (!team) throw new Error(`Team ${options.teamKey} not found`);

  const result = await client.createIssue({
    teamId: team.id,
    title: options.title,
    description: options.description,
    priority: options.priority ?? 0,
    estimate: options.estimate,
    labelIds: options.labelIds,
    assigneeId: options.assigneeId,
  });

  if (!result.success) {
    throw new Error("Failed to create issue");
  }

  return result.issue;
}
```

### Step 2: Update Issues
```typescript
async function updateIssue(
  issueId: string,
  updates: {
    title?: string;
    description?: string;
    priority?: number;
    stateId?: string;
    assigneeId?: string;
    estimate?: number;
  }
) {
  const result = await client.updateIssue(issueId, updates);

  if (!result.success) {
    throw new Error("Failed to update issue");
  }

  return result.issue;
}

// Update by identifier (e.g., "ENG-123")
async function updateByIdentifier(identifier: string, updates: Record<string, unknown>) {
  const issue = await client.issue(identifier);
  return client.updateIssue(issue.id, updates);
}
```

### Step 3: State Transitions
```typescript
async function getWorkflowStates(teamKey: string) {
  const teams = await client.teams({ filter: { key: { eq: teamKey } } });
  const team = teams.nodes[0];

  const states = await team.states();
  return states.nodes.sort((a, b) => a.position - b.position);
}

async function transitionIssue(issueId: string, stateName: string) {
  const issue = await client.issue(issueId);
  const team = await issue.team;
  const states = await team?.states();

  const targetState = states?.nodes.find(
    s => s.name.toLowerCase() === stateName.toLowerCase()
  );

  if (!targetState) {
    throw new Error(`State "${stateName}" not found`);
  }

  return client.updateIssue(issueId, { stateId: targetState.id });
}

// Common transitions
async function markInProgress(issueId: string) {
  return transitionIssue(issueId, "In Progress");
}

async function markDone(issueId: string) {
  return transitionIssue(issueId, "Done");
}
```

### Step 4: Issue Relationships
```typescript
// Create sub-issue
async function createSubIssue(parentId: string, title: string) {
  const parent = await client.issue(parentId);
  const team = await parent.team;

  return client.createIssue({
    teamId: team!.id,
    title,
    parentId,
  });
}

// Link issues (blocking relationship)
async function addBlockingRelation(blockingId: string, blockedById: string) {
  return client.createIssueRelation({
    issueId: blockingId,
    relatedIssueId: blockedById,
    type: "blocks",
  });
}

// Get sub-issues
async function getSubIssues(parentId: string) {
  const parent = await client.issue(parentId);
  const children = await parent.children();
  return children.nodes;
}
```

### Step 5: Comments and Activity
```typescript
async function addComment(issueId: string, body: string) {
  return client.createComment({
    issueId,
    body,
  });
}

async function getComments(issueId: string) {
  const issue = await client.issue(issueId);
  const comments = await issue.comments();
  return comments.nodes;
}
```

## Output

- Issue creation with all metadata
- Bulk update capabilities
- State transition handling
- Parent/child relationships
- Blocking relationships
- Comments and activity

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Issue not found` | Invalid ID or identifier | Verify issue exists |
| `State not found` | Team workflow mismatch | List states for correct team |
| `Validation error` | Invalid field value | Check field constraints |
| `Circular dependency` | Self-blocking issue | Validate relationships |

## Examples

### Complete Issue Creation Flow
```typescript
async function createFeatureIssue(options: {
  teamKey: string;
  title: string;
  description: string;
  priority: 1 | 2 | 3 | 4;
}) {
  // Get team and default state
  const teams = await client.teams({ filter: { key: { eq: options.teamKey } } });
  const team = teams.nodes[0];

  // Get "Backlog" state
  const states = await team.states();
  const backlog = states.nodes.find(s => s.name === "Backlog");

  // Create issue
  const result = await client.createIssue({
    teamId: team.id,
    title: options.title,
    description: options.description,
    priority: options.priority,
    stateId: backlog?.id,
  });

  const issue = await result.issue;

  // Add initial comment
  await client.createComment({
    issueId: issue!.id,
    body: "Issue created via API integration",
  });

  return issue;
}
```
