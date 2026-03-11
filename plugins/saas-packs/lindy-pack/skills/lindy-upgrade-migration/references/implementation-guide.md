# Lindy Upgrade Migration - Implementation Guide

# Lindy Upgrade & Migration

## Overview
Guide for safely upgrading Lindy SDK versions and migrating configurations.

## Prerequisites
- Current SDK version identified
- Changelog reviewed for target version
- Backup of current configuration
- Test environment available

## Instructions

### Step 1: Check Current Version
```bash
# Check installed version
npm list @lindy-ai/sdk

# Check latest available
npm view @lindy-ai/sdk version

# View changelog
npm view @lindy-ai/sdk changelog
```

### Step 2: Review Breaking Changes
```typescript
// Common breaking changes by version

// v1.x -> v2.x
// - Client initialization changed
// Before: new Lindy(apiKey)
// After:  new Lindy({ apiKey })

// - Agent.run() signature changed
// Before: agent.run(input)
// After:  lindy.agents.run(agentId, { input })

// - Events renamed
// Before: 'complete'
// After:  'completed'
```

### Step 3: Update Dependencies
```bash
# Update to latest
npm install @lindy-ai/sdk@latest

# Or specific version
npm install @lindy-ai/sdk@2.0.0

# Check for peer dependency warnings
npm ls @lindy-ai/sdk
```

### Step 4: Update Code
```typescript
// Migration script for v1 -> v2

// Old code (v1)
import Lindy from '@lindy-ai/sdk';
const client = new Lindy(process.env.LINDY_API_KEY);
const result = await client.runAgent('agt_123', 'Hello');

// New code (v2)
import { Lindy } from '@lindy-ai/sdk';
const client = new Lindy({ apiKey: process.env.LINDY_API_KEY });
const result = await client.agents.run('agt_123', { input: 'Hello' });
```

### Step 5: Run Migration Tests
```typescript
// tests/migration.test.ts
import { Lindy } from '@lindy-ai/sdk';

describe('SDK Migration', () => {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  test('client initialization works', async () => {
    const user = await lindy.users.me();
    expect(user.email).toBeDefined();
  });

  test('agent operations work', async () => {
    const agents = await lindy.agents.list();
    expect(Array.isArray(agents)).toBe(true);
  });

  test('run operations work', async () => {
    const result = await lindy.agents.run('agt_test', {
      input: 'Test migration',
    });
    expect(result.output).toBeDefined();
  });
});
```

## Migration Checklist
```markdown
[ ] Backup current configuration
[ ] Review changelog for breaking changes
[ ] Update package.json
[ ] Run npm install
[ ] Update import statements
[ ] Update client initialization
[ ] Update method calls
[ ] Run test suite
[ ] Test in staging environment
[ ] Deploy to production
[ ] Monitor for issues
```

## Output
- Updated SDK to target version
- Migrated code patterns
- Passing test suite
- Documented changes

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import error | Named exports changed | Check new import syntax |
| Type error | Interface changed | Update TypeScript types |
| Runtime error | Method signature changed | Check new API |

## Examples

### Automated Migration Script
```bash
#!/bin/bash
# migrate-lindy.sh

echo "Starting Lindy SDK migration..."

# Backup
cp package.json package.json.backup
cp -r src src.backup

# Update
npm install @lindy-ai/sdk@latest

# Run tests
npm test

if [ $? -eq 0 ]; then
  echo "Migration successful!"
  rm -rf src.backup package.json.backup
else
  echo "Migration failed. Rolling back..."
  mv package.json.backup package.json
  rm -rf src && mv src.backup src
  npm install
  exit 1
fi
```

## Resources
- [Lindy Changelog](https://docs.lindy.ai/changelog)
- [Migration Guide](https://docs.lindy.ai/migration)
- [SDK Reference](https://docs.lindy.ai/sdk)

## Next Steps
Proceed to Pro tier skills for advanced features.
