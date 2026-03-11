---
name: linear-ci-integration
description: |
  Configure Linear CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Linear sync into your build process.
  Trigger with phrases like "linear CI", "linear GitHub Actions",
  "linear automated tests", "CI linear pipeline", "linear CI/CD".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear CI Integration

## Overview
Integrate Linear into your CI/CD pipeline for automated testing and deployment tracking.

## Prerequisites
- GitHub repository with Actions enabled
- Linear API key for CI
- npm/pnpm project configured

## Instructions

### Step 1: Store Secrets in GitHub
```bash
# Using GitHub CLI
gh secret set LINEAR_API_KEY --body "lin_api_xxxxxxxxxxxx"
gh secret set LINEAR_WEBHOOK_SECRET --body "your_webhook_secret"

# Or use GitHub web UI:
# Settings > Secrets and variables > Actions > New repository secret
```

### Step 2: Create Test Workflow
```yaml
# .github/workflows/linear-integration.yml
name: Linear Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run Linear integration tests
        run: npm run test:linear
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results/
```

### Step 3: Create Integration Test Suite
```typescript
// tests/linear.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { LinearClient } from "@linear/sdk";

describe("Linear Integration", () => {
  let client: LinearClient;
  let testTeamId: string;
  const createdIssueIds: string[] = [];

  beforeAll(async () => {
    const apiKey = process.env.LINEAR_API_KEY;
    if (!apiKey) {
      throw new Error("LINEAR_API_KEY required for integration tests");
    }

    client = new LinearClient({ apiKey });

    // Get test team
    const teams = await client.teams();
    testTeamId = teams.nodes[0].id;
  });

  afterAll(async () => {
    // Cleanup test issues
    for (const id of createdIssueIds) {
      try {
        await client.deleteIssue(id);
      } catch {
        // Ignore cleanup errors
      }
    }
  });

  it("should authenticate successfully", async () => {
    const viewer = await client.viewer;
    expect(viewer.name).toBeDefined();
    expect(viewer.email).toBeDefined();
  });

  it("should create an issue", async () => {
    const result = await client.createIssue({
      teamId: testTeamId,
      title: `[CI Test] ${new Date().toISOString()}`,
      description: "Created by CI pipeline",
    });

    expect(result.success).toBe(true);
    const issue = await result.issue;
    expect(issue?.identifier).toBeDefined();

    if (issue) createdIssueIds.push(issue.id);
  });

  it("should query issues", async () => {
    const issues = await client.issues({ first: 10 });
    expect(issues.nodes.length).toBeGreaterThan(0);
  });
});
```

### Step 4: PR Status Updates
```yaml
# .github/workflows/linear-pr-status.yml
name: Update Linear Issues from PR

on:
  pull_request:
    types: [opened, closed, merged]

jobs:
  update-linear:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract Linear Issue ID
        id: extract
        run: |
          # Extract issue identifier from branch name (e.g., feature/ENG-123-description)
          BRANCH_NAME="${{ github.head_ref }}"
          ISSUE_ID=$(echo "$BRANCH_NAME" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          echo "issue_id=$ISSUE_ID" >> $GITHUB_OUTPUT

      - name: Update Linear Issue
        if: steps.extract.outputs.issue_id
        run: |
          npx ts-node scripts/update-linear-from-pr.ts \
            --issue "${{ steps.extract.outputs.issue_id }}" \
            --pr "${{ github.event.pull_request.number }}" \
            --action "${{ github.event.action }}"
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
```

### Step 5: Update Script
```typescript
// scripts/update-linear-from-pr.ts
import { LinearClient } from "@linear/sdk";
import { parseArgs } from "util";

const { values } = parseArgs({
  options: {
    issue: { type: "string" },
    pr: { type: "string" },
    action: { type: "string" },
  },
});

async function main() {
  const client = new LinearClient({
    apiKey: process.env.LINEAR_API_KEY!,
  });

  const issue = await client.issue(values.issue!);

  // Add PR link to issue
  await client.createComment({
    issueId: issue.id,
    body: `PR #${values.pr} ${values.action}: https://github.com/${process.env.GITHUB_REPOSITORY}/pull/${values.pr}`,
  });

  // Update issue state based on PR action
  if (values.action === "opened") {
    // Move to "In Review" state
    const team = await issue.team;
    const states = await team?.states();
    const reviewState = states?.nodes.find(s =>
      s.name.toLowerCase().includes("review")
    );
    if (reviewState) {
      await client.updateIssue(issue.id, { stateId: reviewState.id });
    }
  } else if (values.action === "closed" || values.action === "merged") {
    // Move to "Done" state
    const team = await issue.team;
    const states = await team?.states();
    const doneState = states?.nodes.find(s => s.type === "completed");
    if (doneState) {
      await client.updateIssue(issue.id, { stateId: doneState.id });
    }
  }
}

main().catch(console.error);
```

### Step 6: Create Issues from CI Failures
```yaml
# .github/workflows/create-issue-on-failure.yml
name: Create Linear Issue on Test Failure

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  create-issue:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: Create Linear Issue
        run: |
          curl -X POST https://api.linear.app/graphql \
            -H "Authorization: ${{ secrets.LINEAR_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "query": "mutation { issueCreate(input: { teamId: \"${{ vars.LINEAR_TEAM_ID }}\", title: \"[CI] Build failure: ${{ github.event.workflow_run.head_branch }}\", description: \"Build failed: ${{ github.event.workflow_run.html_url }}\", priority: 1 }) { success } }"
            }'
```

## Output
- Automated test pipeline
- PR-to-issue linking
- Automatic state transitions
- Failure issue creation
- Test result artifacts

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Secret not found` | Missing GitHub secret | Add LINEAR_API_KEY to repository secrets |
| `Issue not found` | Invalid issue identifier | Verify branch naming convention |
| `Permission denied` | Insufficient API key scope | Regenerate API key with write access |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Linear GitHub Integration](https://linear.app/docs/github)
- [Linear API Authentication](https://developers.linear.app/docs/graphql/authentication)

## Next Steps
Configure deployment integration with `linear-deploy-integration`.

## Examples

**Basic usage**: Apply linear ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear ci integration for production environments with multiple constraints and team-specific requirements.