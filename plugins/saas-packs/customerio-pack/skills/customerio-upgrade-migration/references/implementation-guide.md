# Customer.io Upgrade & Migration - Implementation Guide

### Step 1: Assess Current State
```bash
#!/bin/bash
# assess-customerio.sh

echo "=== Customer.io SDK Assessment ==="

# Node.js SDK
echo "Node.js SDK:"
npm list @customerio/track 2>/dev/null || echo "Not installed"
npm list customerio-node 2>/dev/null || echo "Legacy SDK not installed"

# Python SDK
echo -e "\nPython SDK:"
pip show customerio 2>/dev/null || echo "Not installed"

# Check for latest versions
echo -e "\nLatest versions available:"
npm view @customerio/track version 2>/dev/null
pip index versions customerio 2>/dev/null | head -1
```

### Step 2: Review Breaking Changes
```markdown
## Customer.io SDK Changelog Review

### @customerio/track (Node.js)
- v1.x -> v2.x: Updated to ESM modules
- v2.x -> v3.x: Changed region configuration

### customerio (Python)
- v1.x -> v2.x: Async client support added

### API Changes
- Check https://customer.io/docs/changelog/
```

### Step 3: Create Migration Plan
```typescript
// migration-plan.ts
interface MigrationPlan {
  currentVersion: string;
  targetVersion: string;
  breakingChanges: string[];
  codeChanges: CodeChange[];
  testCases: string[];
  rollbackProcedure: string[];
  timeline: Timeline;
}

const migrationPlan: MigrationPlan = {
  currentVersion: '1.2.0',
  targetVersion: '2.0.0',
  breakingChanges: [
    'Region now required in constructor',
    'Event data structure changed',
    'Error types updated'
  ],
  codeChanges: [
    {
      file: 'lib/customerio.ts',
      before: `new TrackClient(siteId, apiKey)`,
      after: `new TrackClient(siteId, apiKey, { region: RegionUS })`
    },
    {
      file: 'lib/customerio.ts',
      before: `client.track(userId, eventName, data)`,
      after: `client.track(userId, { name: eventName, data })`
    }
  ],
  testCases: [
    'Identify user creates/updates profile',
    'Track event records in activity',
    'Error handling catches API errors',
    'Rate limiting respects limits'
  ],
  rollbackProcedure: [
    'Revert package.json to previous version',
    'Run npm install',
    'Deploy previous container image',
    'Verify with smoke tests'
  ],
  timeline: {
    preparation: '1 day',
    staging: '2 days',
    production: '1 day',
    monitoring: '3 days'
  }
};
```

### Step 4: Update Dependencies
```bash
# Upgrade Node.js SDK
npm install @customerio/track@latest

# Or upgrade to specific version
npm install @customerio/track@2.0.0

# Upgrade Python SDK
pip install --upgrade customerio

# Or specific version
pip install customerio==2.0.0
```

### Step 5: Update Code for Breaking Changes
```typescript
// Before (v1.x)
import { CustomerIO } from 'customerio-node';
const cio = new CustomerIO(siteId, apiKey);
await cio.track(userId, 'event_name', { key: 'value' });

// After (v2.x - @customerio/track)
import { TrackClient, RegionUS } from '@customerio/track';
const client = new TrackClient(siteId, apiKey, { region: RegionUS });
await client.track(userId, { name: 'event_name', data: { key: 'value' } });
```

### Step 6: Migration Test Suite
```typescript
// tests/migration.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { TrackClient, RegionUS } from '@customerio/track';

describe('Customer.io Migration Tests', () => {
  let client: TrackClient;

  beforeAll(() => {
    client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  });

  it('should identify user with new SDK', async () => {
    await expect(
      client.identify('migration-test-user', {
        email: 'migration@test.com',
        _migration_test: true
      })
    ).resolves.not.toThrow();
  });

  it('should track event with new format', async () => {
    await expect(
      client.track('migration-test-user', {
        name: 'migration_test_event',
        data: { version: '2.0.0' }
      })
    ).resolves.not.toThrow();
  });

  it('should handle errors correctly', async () => {
    const badClient = new TrackClient('invalid', 'invalid', { region: RegionUS });
    await expect(
      badClient.identify('test', { email: 'test@test.com' })
    ).rejects.toThrow();
  });
});
```

### Step 7: Staged Rollout
```typescript
// lib/feature-flags.ts
const migrationFlags = {
  useNewSDK: process.env.USE_NEW_CIO_SDK === 'true',
  newSDKPercentage: parseInt(process.env.NEW_SDK_PERCENTAGE || '0', 10)
};

// Gradually roll out new SDK
function shouldUseNewSDK(userId: string): boolean {
  if (!migrationFlags.useNewSDK) return false;

  // Hash-based percentage rollout
  const hash = userId.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);

  return Math.abs(hash % 100) < migrationFlags.newSDKPercentage;
}

// Usage
if (shouldUseNewSDK(userId)) {
  await newClient.identify(userId, attributes);
} else {
  await legacyClient.identify(userId, attributes);
}
```

### Step 8: Post-Migration Verification
```bash
#!/bin/bash
# verify-migration.sh

echo "=== Post-Migration Verification ==="

# Check new SDK is installed
echo "SDK Version:"
npm list @customerio/track

# Run smoke tests
echo -e "\nRunning smoke tests..."
npm run test:customerio

# Check error rates
echo -e "\nError rates (last 1 hour):"
# Query your monitoring system here

# Check delivery rates
echo -e "\nDelivery metrics:"
# Query Customer.io reporting API or dashboard
```
