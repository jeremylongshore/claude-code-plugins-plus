---
name: linear-upgrade-migration
description: |
  Upgrade Linear SDK versions and handle breaking changes safely.
  Use when updating to a new SDK version, handling deprecations,
  or migrating between API versions.
  Trigger: "upgrade linear SDK", "linear SDK migration",
  "update linear", "linear breaking changes", "linear deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, migration]

---
# Linear Upgrade Migration

## Overview
Safely upgrade `@linear/sdk` versions with zero downtime. The SDK is auto-generated from Linear's GraphQL schema -- major versions can rename fields, change return types, add required parameters, or remove deprecated methods. This skill covers version checking, upgrade procedure, compatibility layers, and rollback.

## Prerequisites
- Existing Linear integration with version control (Git)
- Test suite covering Linear SDK operations
- Understanding of semantic versioning

## Instructions

### Step 1: Check Current vs Latest Version
```bash
set -euo pipefail
# Current installed version
npm list @linear/sdk 2>/dev/null || echo "Not installed"

# Latest available
npm view @linear/sdk version

# All recent versions
npm view @linear/sdk versions --json | jq '.[-10:]'
```

### Step 2: Review Changelog for Breaking Changes
```bash
set -euo pipefail
# View SDK changelog on GitHub
npm view @linear/sdk repository.url
# Then check: https://github.com/linear/linear/blob/master/packages/sdk/CHANGELOG.md

# Also review Linear's API changelog:
# https://linear.app/changelog (filter for API/developer updates)
```

Common breaking changes between major versions:
- **Renamed fields**: e.g., `issue.state` property vs lazy relation
- **Changed return types**: direct value to paginated connection
- **New required parameters**: mutations gaining mandatory fields
- **Removed methods**: deprecated methods dropped
- **ESM/CJS**: module system changes

### Step 3: Create Upgrade Branch and Install
```bash
set -euo pipefail
git checkout -b upgrade/linear-sdk-$(npm view @linear/sdk version)
npm install @linear/sdk@latest

# Immediately check for type errors
npx tsc --noEmit 2>&1 | head -50
```

### Step 4: Fix Type Errors with Compatibility Layer
```typescript
// src/linear-compat.ts
// Bridge pattern for gradual migration across SDK versions

import { LinearClient } from "@linear/sdk";

/**
 * Normalize issue state access across SDK versions.
 * SDK v2: issue.state was a direct string property
 * SDK v3+: issue.state is a lazy-loaded WorkflowState relation
 */
export async function getIssueStateName(issue: any): Promise<string> {
  if (typeof issue.state === "string") return issue.state;
  const state = await issue.state;
  return state?.name ?? "unknown";
}

export async function getIssueStateType(issue: any): Promise<string> {
  if (typeof issue.stateType === "string") return issue.stateType;
  const state = await issue.state;
  return state?.type ?? "unknown";
}

/**
 * Normalize team access — some versions changed from direct to paginated.
 */
export async function getTeamByKey(client: LinearClient, key: string) {
  const teams = await client.teams({ filter: { key: { eq: key } } });
  return teams.nodes[0];
}

/**
 * Normalize issue creation return — handle both success shapes.
 */
export async function createIssue(
  client: LinearClient,
  input: { teamId: string; title: string; [key: string]: any }
) {
  const result = await client.createIssue(input);
  // Some versions return { success, issue } others return directly
  if ("success" in result) {
    return { success: result.success, issue: await result.issue };
  }
  return { success: true, issue: result };
}
```

### Step 5: Run Tests and Fix Failures
```bash
set -euo pipefail
# Type-check
npx tsc --noEmit

# Run unit tests
npm test

# Run integration tests (if API key available)
npm run test:integration 2>&1 || true

# Lint
npm run lint 2>&1 || true
```

Common fixes:
```typescript
// Fix: Property 'x' does not exist
// Old: issue.statusName
// New: (await issue.state)?.name

// Fix: Type 'X' is not assignable to type 'Y'
// Old: const states: string[] = team.states
// New: const states = await team.states()

// Fix: Expected 2 arguments but got 1
// Check if mutation added required parameter
// Old: client.updateIssue(id, { title: "new" })
// New: client.updateIssue(id, { title: "new" })  // usually same
```

### Step 6: Test in Staging Before Production
```bash
set -euo pipefail
# Deploy to staging
npm run build
npm run deploy:staging

# Run integration tests against staging
LINEAR_API_KEY=$STAGING_LINEAR_API_KEY npm run test:integration

# Check health endpoint
curl -s https://staging.yourapp.com/health/linear | jq .
```

### Step 7: Deploy with Rollback Plan
```bash
set -euo pipefail
# Commit upgrade
git add package.json package-lock.json src/linear-compat.ts
git commit -m "chore: upgrade @linear/sdk to $(npm list @linear/sdk --json | jq -r '.dependencies["@linear/sdk"].version')"
git push origin upgrade/linear-sdk-*

# If something breaks in production:
git revert HEAD
npm install  # Restores previous version
npm run deploy
```

## Version Compatibility

| SDK Range | Node.js | TypeScript | Notable Changes |
|-----------|---------|------------|-----------------|
| 1.x | 14+ | 4.5+ | Initial release, callback-style |
| 2.x-16.x | 16+ | 4.7+ | ESM support, typed models |
| 17.x-28.x | 18+ | 5.0+ | Strict types, new entity models |
| Latest | 18+ | 5.0+ | Refresh tokens, initiatives, agents |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Property does not exist` | Renamed field | Check changelog, update field name |
| `Type is not assignable` | Changed return type | Update type annotations |
| `Module not found` | ESM/CJS mismatch | Update import syntax or `tsconfig` |
| `Cannot find name` | Removed export | Replace with new API equivalent |
| Tests pass, prod fails | SDK version mismatch in lockfile | Delete `node_modules`, `npm ci` |

## Examples

### Pre-Upgrade Audit Script
```typescript
// scripts/audit-linear-usage.ts
// Run before upgrading to find all SDK touchpoints

import { readFileSync } from "fs";
import { globSync } from "glob";

const files = globSync("src/**/*.ts");
const patterns = [
  /LinearClient/g,
  /client\.issues/g,
  /client\.createIssue/g,
  /client\.updateIssue/g,
  /\.state\b/g,
  /\.assignee\b/g,
  /rawRequest/g,
];

for (const file of files) {
  const content = readFileSync(file, "utf-8");
  for (const pattern of patterns) {
    const matches = content.match(pattern);
    if (matches) {
      console.log(`${file}: ${pattern.source} (${matches.length} occurrences)`);
    }
  }
}
```

## Resources
- [SDK Changelog](https://github.com/linear/linear/blob/master/packages/sdk/CHANGELOG.md)
- [API Changelog](https://linear.app/changelog)
- [SDK npm Page](https://www.npmjs.com/package/@linear/sdk)
