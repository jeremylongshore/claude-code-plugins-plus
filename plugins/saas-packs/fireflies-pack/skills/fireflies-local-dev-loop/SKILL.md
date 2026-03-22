---
name: fireflies-local-dev-loop
description: |
  Configure local development workflow for Fireflies.ai GraphQL integrations.
  Use when setting up a development environment, mocking transcript data,
  or establishing a fast iteration cycle with the Fireflies API.
  Trigger with phrases like "fireflies dev setup", "fireflies local development",
  "fireflies dev environment", "develop with fireflies", "mock fireflies".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, testing, workflow]

---
# Fireflies.ai Local Dev Loop

## Overview
Set up a fast local development workflow for Fireflies.ai integrations: project structure, mock data for offline development, test helpers, and API response recording for replay.

## Prerequisites
- Completed `fireflies-install-auth` setup
- Node.js 18+ with npm/pnpm
- Vitest for testing

## Instructions

### Step 1: Project Structure
```
my-fireflies-app/
  src/
    lib/
      fireflies-client.ts    # GraphQL client (see fireflies-sdk-patterns)
      transcript-service.ts  # Business logic layer
    types/
      fireflies.ts           # TypeScript interfaces
  tests/
    fixtures/
      transcript.json        # Recorded API responses
    fireflies-client.test.ts
    transcript-service.test.ts
  .env.local                 # FIREFLIES_API_KEY (git-ignored)
  .env.example               # Template without secrets
```

### Step 2: Record Real API Responses as Fixtures
```typescript
// scripts/record-fixtures.ts
import { FirefliesClient } from "../src/lib/fireflies-client";
import { writeFileSync, mkdirSync } from "fs";

async function recordFixtures() {
  const client = new FirefliesClient();
  mkdirSync("tests/fixtures", { recursive: true });

  // Record user
  const user = await client.query(`{ user { name email user_id is_admin } }`);
  writeFileSync("tests/fixtures/user.json", JSON.stringify(user, null, 2));

  // Record transcript list
  const list = await client.query(`{
    transcripts(limit: 3) {
      id title date duration organizer_email
      summary { overview action_items keywords }
    }
  }`);
  writeFileSync("tests/fixtures/transcripts.json", JSON.stringify(list, null, 2));

  // Record single transcript with sentences
  const id = list.transcripts[0]?.id;
  if (id) {
    const full = await client.query(`
      query($id: String!) {
        transcript(id: $id) {
          id title date duration
          speakers { id name }
          sentences { speaker_name text start_time end_time }
          summary { overview action_items keywords }
          analytics {
            sentiments { positive_pct negative_pct neutral_pct }
            speakers { name duration word_count }
          }
        }
      }
    `, { id });
    writeFileSync("tests/fixtures/transcript-full.json", JSON.stringify(full, null, 2));
  }

  console.log("Fixtures recorded in tests/fixtures/");
}

recordFixtures().catch(console.error);
```

### Step 3: Mock Client for Tests
```typescript
// tests/helpers/mock-fireflies.ts
import { readFileSync } from "fs";

export function createMockClient() {
  const fixtures: Record<string, any> = {};

  return {
    loadFixture(name: string) {
      fixtures[name] = JSON.parse(
        readFileSync(`tests/fixtures/${name}.json`, "utf-8")
      );
    },

    async query(gql: string, variables?: Record<string, any>) {
      // Match query to fixture by operation
      if (gql.includes("transcripts(")) return fixtures["transcripts"];
      if (gql.includes("transcript(id:")) return fixtures["transcript-full"];
      if (gql.includes("user {")) return fixtures["user"];
      throw new Error(`No fixture for query: ${gql.slice(0, 50)}`);
    },
  };
}
```

### Step 4: Write Tests
```typescript
// tests/transcript-service.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMockClient } from "./helpers/mock-fireflies";

describe("Transcript Service", () => {
  let mockClient: ReturnType<typeof createMockClient>;

  beforeEach(() => {
    mockClient = createMockClient();
    mockClient.loadFixture("transcripts");
    mockClient.loadFixture("transcript-full");
  });

  it("should list recent transcripts", async () => {
    const data = await mockClient.query("{ transcripts(limit: 3) { id title } }");
    expect(data.transcripts).toBeDefined();
    expect(data.transcripts.length).toBeGreaterThan(0);
  });

  it("should fetch full transcript with sentences", async () => {
    const data = await mockClient.query(
      `query($id: String!) { transcript(id: $id) { sentences { text } } }`,
      { id: "test-id" }
    );
    expect(data.transcript.sentences).toBeDefined();
  });

  it("should handle API errors gracefully", async () => {
    const errorClient = {
      query: vi.fn().mockRejectedValue(new Error("Fireflies: auth_failed")),
    };
    await expect(errorClient.query("{ user { email } }"))
      .rejects.toThrow("auth_failed");
  });
});
```

### Step 5: Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "record-fixtures": "tsx scripts/record-fixtures.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

### Step 6: Environment Setup
```bash
set -euo pipefail
# Create .env from template
cp .env.example .env.local

# .env.example
echo 'FIREFLIES_API_KEY=your-key-here' > .env.example

# .gitignore additions
echo '.env.local' >> .gitignore
echo 'tests/fixtures/*.json' >> .gitignore
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Fixture not found | Fixtures not recorded | Run `npm run record-fixtures` |
| Auth error in tests | Using real API key in CI | Use mock client, not real API |
| Type mismatch | API schema changed | Re-record fixtures, update types |
| Rate limit during recording | Too many fixture requests | Record once, commit fixtures |

## Output
- Project structure with typed client and service layers
- Recorded API fixtures for offline testing
- Mock client for unit tests
- Dev scripts with hot reload and watch mode

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [Fireflies API Docs](https://docs.fireflies.ai/)

## Next Steps
See `fireflies-sdk-patterns` for production-ready client patterns.
