---
name: linear-local-dev-loop
description: |
  Set up local Linear development environment and testing workflow.
  Use when configuring local development, testing integrations,
  or setting up a development workflow with Linear.
  Trigger with phrases like "linear local development", "linear dev setup",
  "test linear locally", "linear development environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Local Dev Loop

## Overview
Set up an efficient local development workflow for Linear integrations.

## Prerequisites
- Node.js 18+ with TypeScript
- Linear SDK installed
- Separate Linear workspace for development (recommended)
- ngrok or similar for webhook testing

## Instructions

### Step 1: Project Setup
```bash
set -euo pipefail
# Initialize project
mkdir linear-integration && cd linear-integration
npm init -y
npm install @linear/sdk typescript ts-node dotenv
npm install -D @types/node vitest

# Create tsconfig.json
npx tsc --init --target ES2022 --module NodeNext --moduleResolution NodeNext
```

### Step 2: Environment Configuration
```bash
# Create .env for local development
cat > .env << 'EOF'
LINEAR_API_KEY=lin_api_dev_xxxxxxxxxxxx
LINEAR_WEBHOOK_SECRET=your_webhook_secret
NODE_ENV=development
EOF

# Create .env.example (commit this)
cat > .env.example << 'EOF'
LINEAR_API_KEY=lin_api_xxxxxxxxxxxx
LINEAR_WEBHOOK_SECRET=
NODE_ENV=development
EOF

# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

### Step 3: Create Development Client
```typescript
// src/client.ts
import { LinearClient } from "@linear/sdk";
import dotenv from "dotenv";

dotenv.config();

export const linearClient = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY!,
});

export async function verifyClient(): Promise<boolean> {
  try {
    const viewer = await linearClient.viewer;
    console.log(`[Linear] Connected as ${viewer.name}`);
    return true;
  } catch (error) {
    console.error("[Linear] Connection failed:", error);
    return false;
  }
}
```

### Step 4: Create Test Utilities
```typescript
// src/test-utils.ts
import { linearClient } from "./client";

export async function createTestIssue(teamKey: string) {
  const teams = await linearClient.teams();
  const team = teams.nodes.find(t => t.key === teamKey);

  if (!team) throw new Error(`Team ${teamKey} not found`);

  const result = await linearClient.createIssue({
    teamId: team.id,
    title: `[TEST] ${new Date().toISOString()}`,
    description: "Automated test issue - safe to delete",
  });

  return result.issue;
}

export async function cleanupTestIssues(teamKey: string) {
  const issues = await linearClient.issues({
    filter: {
      team: { key: { eq: teamKey } },
      title: { startsWith: "[TEST]" },
    },
  });

  for (const issue of issues.nodes) {
    await issue.delete();
  }

  console.log(`Cleaned up ${issues.nodes.length} test issues`);
}
```

### Step 5: Set Up Watch Mode
```json
// package.json scripts
{
  "scripts": {
    "dev": "ts-node --watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "verify": "ts-node src/verify.ts"
  }
}
```

## Output
- Local development environment ready
- Environment variables configured
- Test utilities for creating/cleaning test data
- Watch mode for rapid iteration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `API key not set` | Missing .env file | Copy .env.example to .env |
| `Cannot find module` | TypeScript config issue | Check tsconfig.json paths |
| `Connection refused` | Network issue | Verify internet connectivity |
| `Webhook not received` | Tunnel not running | Start ngrok tunnel |

## Examples

### Webhook Development with ngrok
```bash
set -euo pipefail
# Terminal 1: Start your webhook server
npm run dev

# Terminal 2: Start ngrok tunnel
ngrok http 3000  # 3000: 3 seconds in ms

# Copy the https URL and add to Linear webhook settings
```

### Integration Test Example
```typescript
// tests/integration.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { createTestIssue, cleanupTestIssues } from "../src/test-utils";

describe("Linear Integration", () => {
  const teamKey = "ENG"; // Your test team

  afterAll(async () => {
    await cleanupTestIssues(teamKey);
  });

  it("should create and fetch an issue", async () => {
    const issue = await createTestIssue(teamKey);
    expect(issue).toBeDefined();
    expect(issue?.title).toContain("[TEST]");
  });
});
```

## Resources
- [Linear SDK TypeScript](https://developers.linear.app/docs/sdk/getting-started)
- [Webhook Development](https://developers.linear.app/docs/graphql/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps
After setting up local dev, proceed to `linear-sdk-patterns` for best practices.