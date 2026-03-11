# Juicebox Upgrade Migration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Assess Current State
```bash
# Check current SDK version
npm list @juicebox/sdk

# Check for available updates
npm outdated @juicebox/sdk

# Review changelog
curl -s https://api.github.com/repos/juicebox-ai/sdk-js/releases/latest | jq '.body'
```

### Step 2: Review Breaking Changes
```typescript
// Common breaking changes between versions

// v1.x -> v2.x Migration
// OLD (v1.x)
const client = new JuiceboxClient(apiKey);
const results = await client.search(query);

// NEW (v2.x)
const client = new JuiceboxClient({ apiKey });
const results = await client.search.people({ query });
```

### Step 3: Create Migration Script
```typescript
// scripts/migrate-juicebox.ts

/**
 * Migration: v1.x -> v2.x
 *
 * Breaking changes:
 * 1. Client constructor now takes options object
 * 2. search() renamed to search.people()
 * 3. Result structure changed
 */

// Step 1: Update imports
// OLD: import JuiceboxClient from '@juicebox/sdk';
// NEW: import { JuiceboxClient } from '@juicebox/sdk';

// Step 2: Update client initialization
function migrateClientInit(code: string): string {
  return code.replace(
    /new JuiceboxClient\((\w+)\)/g,
    'new JuiceboxClient({ apiKey: $1 })'
  );
}

// Step 3: Update method calls
function migrateSearchCalls(code: string): string {
  return code.replace(
    /client\.search\(([^)]+)\)/g,
    'client.search.people({ query: $1 })'
  );
}

// Step 4: Update result handling
function migrateResultAccess(code: string): string {
  return code.replace(
    /results\.data/g,
    'results.profiles'
  );
}
```

### Step 4: Staged Rollout
```typescript
// lib/feature-flags.ts
export class JuiceboxVersionManager {
  private useNewVersion: boolean;

  constructor() {
    this.useNewVersion = process.env.JUICEBOX_USE_V2 === 'true';
  }

  async search(query: string, options?: SearchOptions) {
    if (this.useNewVersion) {
      return this.searchV2(query, options);
    }
    return this.searchV1(query, options);
  }

  private async searchV1(query: string, options?: SearchOptions) {
    // Legacy implementation
  }

  private async searchV2(query: string, options?: SearchOptions) {
    // New implementation
  }
}
```

### Step 5: Validation Testing
```typescript
// tests/migration.test.ts
import { describe, it, expect } from 'vitest';

describe('Migration Validation', () => {
  it('produces equivalent results with new SDK', async () => {
    const query = 'software engineer San Francisco';

    const oldResults = await legacyClient.search(query);
    const newResults = await newClient.search.people({ query });

    // Verify structure matches
    expect(newResults.profiles.length).toBe(oldResults.data.length);

    // Verify data matches
    expect(newResults.profiles[0].name).toBe(oldResults.data[0].name);
  });

  it('handles edge cases correctly', async () => {
    // Test empty results
    // Test error handling
    // Test pagination
  });
});
```

## Migration Checklist

```markdown

## SDK Upgrade Checklist

### Pre-Migration
- [ ] Current version documented
- [ ] Target version identified
- [ ] Changelog reviewed
- [ ] Breaking changes listed
- [ ] Migration script created

### Testing
- [ ] Unit tests updated
- [ ] Integration tests pass
- [ ] Performance benchmarks run
- [ ] Edge cases validated

### Deployment
- [ ] Staged rollout plan
- [ ] Feature flag configured
- [ ] Monitoring in place
- [ ] Rollback plan ready

### Post-Migration
- [ ] Old code removed
- [ ] Feature flag cleaned up
- [ ] Documentation updated
- [ ] Team notified
```

## Rollback Plan

```bash
# Immediate rollback if issues detected
npm install @juicebox/sdk@1.x.x

# Or use feature flag
export JUICEBOX_USE_V2=false
```
