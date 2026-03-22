---
name: fireflies-upgrade-migration
description: |
  Handle Fireflies.ai API deprecations and migrate to current query patterns.
  Use when updating deprecated fields, migrating query patterns,
  or responding to Fireflies API changelog updates.
  Trigger with phrases like "upgrade fireflies", "fireflies deprecated",
  "fireflies migration", "fireflies breaking changes", "fireflies changelog".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api, migration]

---
# Fireflies.ai Upgrade & Migration

## Current State
!`npm list graphql graphql-request 2>/dev/null || echo 'No graphql packages'`

## Overview
Fireflies.ai uses a GraphQL API (no versioned SDK). Breaking changes come as field deprecations and new query parameter patterns. This skill covers all known deprecations and migration paths.

## Known Deprecations

### Transcript Query Parameter Changes
```typescript
// DEPRECATED: Single organizer email string
const OLD = `{ transcripts(organizer_email: "alice@co.com") { id } }`;

// CURRENT: Array of organizer emails
const NEW = `{ transcripts(organizers: ["alice@co.com"]) { id } }`;
```

```typescript
// DEPRECATED: Single participant email string
const OLD = `{ transcripts(participant_email: "bob@co.com") { id } }`;

// CURRENT: Array of participant emails
const NEW = `{ transcripts(participants: ["bob@co.com"]) { id } }`;
```

```typescript
// DEPRECATED: title parameter for search
const OLD = `{ transcripts(title: "standup") { id } }`;

// CURRENT: keyword with scope
const NEW = `{ transcripts(keyword: "standup") { id } }`;
```

```typescript
// DEPRECATED: date parameter (single date)
const OLD = `{ transcripts(date: "2026-03-01") { id } }`;

// CURRENT: fromDate/toDate range
const NEW = `{
  transcripts(
    fromDate: "2026-03-01T00:00:00Z"
    toDate: "2026-03-31T23:59:59Z"
  ) { id }
}`;
```

### Field-Level Deprecations
```typescript
// DEPRECATED
transcript.host_email

// CURRENT
transcript.organizer_email
```

## Migration Procedure

### Step 1: Scan Codebase for Deprecated Patterns
```bash
set -euo pipefail
echo "=== Scanning for deprecated Fireflies patterns ==="

# Deprecated query parameters
grep -rn 'organizer_email:' --include='*.ts' --include='*.js' --include='*.py' . || echo "No organizer_email (good)"
grep -rn 'participant_email:' --include='*.ts' --include='*.js' --include='*.py' . || echo "No participant_email (good)"
grep -rn 'host_email' --include='*.ts' --include='*.js' --include='*.py' . || echo "No host_email (good)"
grep -rn 'transcripts(.*title:' --include='*.ts' --include='*.js' --include='*.py' . || echo "No title param (good)"
grep -rn 'transcripts(.*date:' --include='*.ts' --include='*.js' --include='*.py' . || echo "No date param (good)"
```

### Step 2: Update Query Patterns
Create a migration helper:
```typescript
// migrations/fireflies-deprecations.ts

/**
 * Maps old query parameter names to new ones.
 * Update your GraphQL queries to use the new parameter names.
 */
const PARAM_MIGRATIONS: Record<string, string> = {
  "organizer_email": "organizers (now an array)",
  "participant_email": "participants (now an array)",
  "title": "keyword",
  "date": "fromDate + toDate",
  "host_email": "organizer_email",
};

export function checkForDeprecations(query: string): string[] {
  const warnings: string[] = [];
  for (const [old, replacement] of Object.entries(PARAM_MIGRATIONS)) {
    if (query.includes(old)) {
      warnings.push(`Deprecated: "${old}" → use "${replacement}"`);
    }
  }
  return warnings;
}
```

### Step 3: Introspect Schema for Changes
```bash
set -euo pipefail
# Discover all available query fields
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { queryType { fields { name args { name type { name kind } } } } } }"
  }' | jq '.data.__schema.queryType.fields[] | {name, args: [.args[] | .name]}'

# Discover transcript fields
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"Transcript\") { fields { name type { name kind } } } }"
  }' | jq '.data.__type.fields[] | .name'
```

### Step 4: Test Updated Queries
```typescript
import { describe, it, expect } from "vitest";
import { checkForDeprecations } from "../migrations/fireflies-deprecations";

describe("Deprecation Check", () => {
  it("should flag deprecated parameters", () => {
    const warnings = checkForDeprecations(
      '{ transcripts(organizer_email: "test") { id } }'
    );
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings[0]).toContain("organizers");
  });

  it("should pass clean queries", () => {
    const warnings = checkForDeprecations(
      '{ transcripts(organizers: ["test"]) { id } }'
    );
    expect(warnings.length).toBe(0);
  });
});
```

### Step 5: Monitor Fireflies Changelog
```bash
# Check for API updates
set -euo pipefail
curl -s https://docs.fireflies.ai/additional-info/change-log | head -100
# Or visit: https://docs.fireflies.ai/getting-started/whats-new
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Field not found | Using removed field | Introspect schema, update query |
| Unexpected null | Field renamed | Check deprecation list above |
| Query validation error | Old parameter name | Update to array-based params |
| Type mismatch | String vs array param | Wrap single value in array |

## Output
- Codebase scanned for deprecated patterns
- All queries updated to current API patterns
- Schema introspection results for reference
- Tests verifying updated queries work

## Resources
- [Fireflies Changelog](https://docs.fireflies.ai/additional-info/change-log)
- [Fireflies What's New](https://docs.fireflies.ai/getting-started/whats-new)
- [Fireflies Introspection](https://docs.fireflies.ai/fundamentals/introspection)

## Next Steps
For CI integration during upgrades, see `fireflies-ci-integration`.
