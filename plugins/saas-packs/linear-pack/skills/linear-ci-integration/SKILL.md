---
name: linear-ci-integration
description: |
  Integrate Linear with GitHub Actions CI/CD pipelines.
  Use when setting up automated testing, PR-to-issue linking,
  or creating Linear issues from CI failures.
  Trigger: "linear CI", "linear GitHub Actions", "linear CI/CD",
  "linear automated tests", "linear PR integration".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, testing, ci-cd]

---
# Linear CI Integration

## Overview
Integrate Linear into GitHub Actions CI/CD pipelines: run integration tests against the Linear API, automatically link PRs to issues, transition issue states on PR events, and create Linear issues from build failures.

## Prerequisites
- GitHub repository with Actions enabled
- Linear API key stored as GitHub secret
- npm/pnpm project with `@linear/sdk` configured

## Instructions

### Step 1: Store Secrets in GitHub
```bash
# Using GitHub CLI
gh secret set LINEAR_API_KEY --body "lin_api_xxxxxxxxxxxx"
gh secret set LINEAR_WEBHOOK_SECRET --body "whsec_xxxxxxxxxxxx"

# Store team ID for CI-created issues
gh variable set LINEAR_TEAM_ID --body "team-uuid-here"
```

### Step 2: Integration Test Workflow
```yaml
# .github/workflows/linear-tests.yml
name: Linear Integration Tests

on:
  push:
    branches: [main]
  pull_request:

env:
  LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run test:linear
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/
```

### Step 3: Integration Test Suite
```typescript
// tests/linear.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { LinearClient } from "@linear/sdk";

describe("Linear Integration", () => {
  let client: LinearClient;
  let teamId: string;
  const cleanup: string[] = [];

  beforeAll(async () => {
    const apiKey = process.env.LINEAR_API_KEY;
    if (!apiKey) throw new Error("LINEAR_API_KEY required for integration tests");
    client = new LinearClient({ apiKey });

    const teams = await client.teams();
    teamId = teams.nodes[0].id;
  });

  afterAll(async () => {
    for (const id of cleanup) {
      try { await client.deleteIssue(id); } catch {}
    }
  });

  it("authenticates successfully", async () => {
    const viewer = await client.viewer;
    expect(viewer.name).toBeDefined();
    expect(viewer.email).toBeDefined();
  });

  it("creates an issue", async () => {
    const result = await client.createIssue({
      teamId,
      title: `[CI] ${new Date().toISOString()}`,
      description: "Created by CI pipeline",
    });
    expect(result.success).toBe(true);
    const issue = await result.issue;
    expect(issue?.identifier).toBeDefined();
    if (issue) cleanup.push(issue.id);
  });

  it("queries issues with filtering", async () => {
    const issues = await client.issues({
      first: 10,
      filter: { team: { id: { eq: teamId } } },
    });
    expect(issues.nodes.length).toBeGreaterThan(0);
  });

  it("lists workflow states", async () => {
    const teams = await client.teams();
    const states = await teams.nodes[0].states();
    expect(states.nodes.length).toBeGreaterThan(0);
    expect(states.nodes.some(s => s.type === "completed")).toBe(true);
  });
});
```

### Step 4: PR-to-Issue Linking Workflow
Automatically update Linear issues when PRs are opened, merged, or closed. Extracts issue identifiers from branch names (e.g., `feature/ENG-123-description`).

```yaml
# .github/workflows/linear-pr-sync.yml
name: Sync PR to Linear

on:
  pull_request:
    types: [opened, closed]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Extract Linear issue ID from branch
        id: extract
        run: |
          BRANCH="${{ github.head_ref }}"
          ISSUE_ID=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+' | head -1 || true)
          echo "issue_id=$ISSUE_ID" >> $GITHUB_OUTPUT

      - name: Update Linear issue
        if: steps.extract.outputs.issue_id
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          npx tsx scripts/sync-pr-to-linear.ts \
            --issue "${{ steps.extract.outputs.issue_id }}" \
            --pr "${{ github.event.pull_request.number }}" \
            --action "${{ github.event.action }}" \
            --merged "${{ github.event.pull_request.merged }}"
```

### Step 5: PR Sync Script
```typescript
// scripts/sync-pr-to-linear.ts
import { LinearClient } from "@linear/sdk";
import { parseArgs } from "util";

const { values } = parseArgs({
  options: {
    issue: { type: "string" },
    pr: { type: "string" },
    action: { type: "string" },
    merged: { type: "string" },
  },
});

async function main() {
  const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

  // Find issue by identifier search
  const results = await client.issueSearch(values.issue!);
  const issue = results.nodes[0];
  if (!issue) {
    console.log(`Issue ${values.issue} not found — skipping`);
    return;
  }

  const prUrl = `https://github.com/${process.env.GITHUB_REPOSITORY}/pull/${values.pr}`;

  // Add comment linking to PR
  await client.createComment({
    issueId: issue.id,
    body: `PR #${values.pr} ${values.action}: [View PR](${prUrl})`,
  });

  // Transition state based on PR action
  const team = await issue.team;
  const states = await team!.states();

  if (values.action === "opened") {
    const reviewState = states.nodes.find(s =>
      s.name.toLowerCase().includes("review") || s.name.toLowerCase().includes("in progress")
    );
    if (reviewState) await client.updateIssue(issue.id, { stateId: reviewState.id });
  } else if (values.action === "closed" && values.merged === "true") {
    const doneState = states.nodes.find(s => s.type === "completed");
    if (doneState) await client.updateIssue(issue.id, { stateId: doneState.id });
  }

  console.log(`Updated ${values.issue} for PR #${values.pr} (${values.action})`);
}

main().catch(console.error);
```

### Step 6: Create Issue on CI Failure
```yaml
# .github/workflows/issue-on-failure.yml
name: Create Linear Issue on Failure

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  create-issue:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: Create Linear issue for build failure
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          curl -s -X POST https://api.linear.app/graphql \
            -H "Authorization: $LINEAR_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
              "query": "mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { identifier url } } }",
              "variables": {
                "input": {
                  "teamId": "${{ vars.LINEAR_TEAM_ID }}",
                  "title": "[CI] Build failure: ${{ github.event.workflow_run.head_branch }}",
                  "description": "Build failed on branch `${{ github.event.workflow_run.head_branch }}`.\n\n[View run](${{ github.event.workflow_run.html_url }})",
                  "priority": 1
                }
              }
            }'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Secret not found` | Missing GitHub secret | Add `LINEAR_API_KEY` to repo Settings > Secrets > Actions |
| Issue not found | Wrong identifier or workspace | Verify branch naming convention matches team key |
| `Permission denied` | API key lacks write scope | Regenerate key with write access |
| Duplicate CI issues | Failure workflow runs repeatedly | Add deduplication check before creating |

## Examples

### PR Template for Linear Integration
```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## Linear Issue
<!-- Use magic words: Fixes, Closes, Resolves -->
Fixes ENG-XXX

## Changes
-

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Linear GitHub Integration](https://linear.app/docs/github)
- [Linear API Authentication](https://linear.app/developers/graphql)
