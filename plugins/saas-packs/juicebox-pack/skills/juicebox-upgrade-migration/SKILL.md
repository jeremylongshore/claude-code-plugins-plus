---
name: juicebox-upgrade-migration
description: |
  Manage Juicebox SDK upgrades.
  Use when upgrading SDK versions, migrating between API versions,
  or handling breaking changes.
  Trigger with phrases like "upgrade juicebox", "juicebox migration",
  "update juicebox SDK", "juicebox breaking changes".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

Safely upgrade from one Juicebox SDK version to another. Covers checking current vs. latest version, reviewing breaking changes, applying common migration patterns (renamed endpoints, changed response shapes, new auth format), staged rollout with feature flags, and validation testing to confirm parity.

## Prerequisites

- Current Juicebox SDK version identified (`npm list @juicebox/sdk` or `pip show juicebox-sdk`)
- Git repository with a clean working tree (no uncommitted changes)
- Test environment where you can validate the upgrade before production
- `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` set for integration tests

## Instructions

### Step 1: Check Current vs. Latest Version

```bash
# Node.js SDK
echo "Current:"
npm list @juicebox/sdk 2>/dev/null || echo "Not installed"

echo ""
echo "Latest available:"
npm view @juicebox/sdk version 2>/dev/null || echo "Package not found"

echo ""
echo "All available versions:"
npm view @juicebox/sdk versions --json 2>/dev/null | tail -10

# Python SDK
echo ""
echo "Python current:"
pip show juicebox-sdk 2>/dev/null | grep Version || echo "Not installed"

echo ""
echo "Python latest:"
pip index versions juicebox-sdk 2>/dev/null | head -1 || echo "pip index not available"
```

### Step 2: Review Breaking Changes

Check the changelog for breaking changes between your current and target versions:

```bash
# Fetch release notes from GitHub
curl -s "https://api.github.com/repos/juicebox-ai/sdk-js/releases" \
  | jq -r '.[] | "## \(.tag_name)\n\(.body)\n"' \
  | head -100
```

Common breaking changes across Juicebox SDK versions:

| Version | Breaking Change | Migration |
|---------|----------------|-----------|
| v1 to v2 | Constructor takes options object instead of string | `new JuiceboxClient(key)` becomes `new JuiceboxClient({ apiKey: key })` |
| v1 to v2 | `client.search(query)` renamed | Use `client.search.people({ query })` |
| v1 to v2 | Auth header format changed | `Bearer {token}` becomes `token {username}:{api_token}` |
| v1 to v2 | `results.data` response field renamed | Use `results.profiles` instead |
| v2.0 to v2.1 | `enrichProfile()` returns promise | Add `await` to all enrich calls |
| v2.1 to v2.2 | Merge API integration restructured | Update ATS connector imports |

### Step 3: Create Migration Branch

```bash
# Create a dedicated migration branch
CURRENT_VERSION=$(npm list @juicebox/sdk --json 2>/dev/null | jq -r '.dependencies["@juicebox/sdk"].version // "unknown"')
TARGET_VERSION=$(npm view @juicebox/sdk version 2>/dev/null || echo "latest")
BRANCH_NAME="chore/juicebox-sdk-${CURRENT_VERSION}-to-${TARGET_VERSION}"

git checkout -b "$BRANCH_NAME"
npm install @juicebox/sdk@"${TARGET_VERSION}"
git add package.json package-lock.json
git commit -m "chore: bump @juicebox/sdk from ${CURRENT_VERSION} to ${TARGET_VERSION}"
```

### Step 4: Apply Common Migration Patterns

**Pattern A: Client constructor change (v1 to v2)**

```typescript
// BEFORE (v1.x)
import JuiceboxClient from "@juicebox/sdk";
const client = new JuiceboxClient(process.env.JUICEBOX_API_KEY!);

// AFTER (v2.x)
import { JuiceboxClient } from "@juicebox/sdk";
const client = new JuiceboxClient({
  username: process.env.JUICEBOX_USERNAME!,
  apiToken: process.env.JUICEBOX_API_TOKEN!,
});
```

**Pattern B: Search method restructure (v1 to v2)**

```typescript
// BEFORE (v1.x)
const results = await client.search("senior engineer fintech NYC");
const profiles = results.data;

// AFTER (v2.x)
const results = await client.search.people({
  query: "senior engineer fintech NYC",
  limit: 25,
});
const profiles = results.profiles;
```

**Pattern C: Enrichment now returns promises (v2.0 to v2.1)**

```typescript
// BEFORE (v2.0)
const enriched = client.enrichProfile(profileId);

// AFTER (v2.1+)
const enriched = await client.enrichProfile(profileId);
```

**Automated find-and-fix with sed:**

```bash
# Find all files using old patterns
grep -rn "new JuiceboxClient(" --include="*.ts" --include="*.js" src/
grep -rn "\.search(" --include="*.ts" --include="*.js" src/ | grep -v "search.people"
grep -rn "results\.data" --include="*.ts" --include="*.js" src/
```

### Step 5: Staged Rollout with Feature Flags

```typescript
// lib/juicebox-version-bridge.ts
import { JuiceboxClient as JuiceboxV2 } from "@juicebox/sdk";

interface SearchResult {
  profiles: Array<{ id: string; name: string; title: string; company: string }>;
  total: number;
}

export class JuiceboxBridge {
  private v2Client: JuiceboxV2;
  private useV2: boolean;

  constructor() {
    this.useV2 = process.env.JUICEBOX_USE_V2 === "true";
    this.v2Client = new JuiceboxV2({
      username: process.env.JUICEBOX_USERNAME!,
      apiToken: process.env.JUICEBOX_API_TOKEN!,
    });
  }

  async search(query: string, limit = 25): Promise<SearchResult> {
    if (this.useV2) {
      const result = await this.v2Client.search.people({ query, limit });
      return { profiles: result.profiles, total: result.total };
    }

    // Legacy path -- remove after validation
    const result = await this.legacySearch(query, limit);
    return { profiles: result.data, total: result.total };
  }

  private async legacySearch(query: string, limit: number): Promise<any> {
    // v1 implementation kept for rollback
    const response = await fetch("https://api.juicebox.ai/v1/search", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.JUICEBOX_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query, limit }),
    });
    return response.json();
  }
}
```

Deploy with the feature flag off, then enable gradually:

```bash
# 1. Deploy with v2 disabled
kubectl set env deployment/juicebox-integration JUICEBOX_USE_V2=false

# 2. Enable for canary
kubectl set env deployment/juicebox-integration-canary JUICEBOX_USE_V2=true

# 3. Monitor for 1 hour, then enable for all
kubectl set env deployment/juicebox-integration JUICEBOX_USE_V2=true
```

### Step 6: Validation Testing

```typescript
// tests/migration-validation.test.ts
import { describe, it, expect } from "vitest";
import { JuiceboxBridge } from "../lib/juicebox-version-bridge";

describe("Juicebox SDK Migration Validation", () => {
  const bridge = new JuiceboxBridge();

  it("search returns profiles with expected shape", async () => {
    const result = await bridge.search("software engineer San Francisco", 5);

    expect(result.profiles).toBeDefined();
    expect(result.profiles.length).toBeLessThanOrEqual(5);
    expect(result.total).toBeGreaterThanOrEqual(0);

    if (result.profiles.length > 0) {
      const profile = result.profiles[0];
      expect(profile).toHaveProperty("id");
      expect(profile).toHaveProperty("name");
    }
  });

  it("handles empty results gracefully", async () => {
    const result = await bridge.search("zzzzz_no_results_expected_zzzzz", 1);
    expect(result.profiles).toEqual([]);
    expect(result.total).toBe(0);
  });

  it("auth works with new token format", async () => {
    const response = await fetch("https://api.juicebox.ai/v1/auth/me", {
      headers: {
        "Authorization": `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`,
      },
    });
    expect(response.status).toBe(200);
  });
});
```

Run the tests:

```bash
npx vitest run tests/migration-validation.test.ts
```

## Output

- Migration branch with SDK version bump commit
- Updated import statements and client initialization
- `lib/juicebox-version-bridge.ts` -- feature-flagged bridge between old and new SDK
- `tests/migration-validation.test.ts` -- validation tests confirming response parity
- Rollback path: set `JUICEBOX_USE_V2=false` or `npm install @juicebox/sdk@{old_version}`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TypeError: JuiceboxClient is not a constructor` | v2 uses named export, not default | Change `import JuiceboxClient` to `import { JuiceboxClient }` |
| `results.data is undefined` | v2 renamed `data` to `profiles` | Update all `results.data` references to `results.profiles` |
| `401 Unauthorized` after upgrade | Auth format changed from Bearer to token-based | Update header to `Authorization: token {username}:{api_token}` |
| `search is not a function` | v2 restructured search into `search.people()` | Update `client.search(q)` to `client.search.people({ query: q })` |
| Tests pass locally but fail in CI | CI env vars still use old `JUICEBOX_API_KEY` | Add `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` to CI secrets |

## Examples

**Quick check if upgrade is needed:**

```bash
CURRENT=$(npm list @juicebox/sdk --json 2>/dev/null | jq -r '.dependencies["@juicebox/sdk"].version')
LATEST=$(npm view @juicebox/sdk version)
if [ "$CURRENT" != "$LATEST" ]; then
  echo "Upgrade available: ${CURRENT} -> ${LATEST}"
else
  echo "Already on latest: ${CURRENT}"
fi
```

**Rollback immediately if issues detected:**

```bash
# Revert to old SDK version
npm install @juicebox/sdk@1.x.x

# Or use feature flag for instant rollback (no redeploy)
kubectl set env deployment/juicebox-integration JUICEBOX_USE_V2=false
```

## Resources

- [Juicebox SDK Releases](https://github.com/juicebox-ai/sdk-js/releases)
- [Juicebox Migration Guides](https://juicebox.ai/docs/migration)
- [Juicebox API Changelog](https://juicebox.ai/docs/changelog)

## Next Steps

After the upgrade is validated, remove the feature flag bridge and legacy code paths. Run `juicebox-prod-checklist` to verify production readiness before the final deployment.
