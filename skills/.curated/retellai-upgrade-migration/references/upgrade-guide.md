# Upgrade Guide

## Import Changes

```typescript
// Before (v1.x)
import { Client } from '@retellai/sdk';

// After (v2.x)
import { RetellAIClient } from '@retellai/sdk';
```

## Configuration Changes

```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new RetellAIClient({
  apiKey: 'xxx',
});
```

## Rollback Procedure

```bash
set -euo pipefail
npm install @retellai/sdk@1.x.x --save-exact
```

## Deprecation Monitoring

```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Retell AI]', warning.message);
      // Log to tracking system for proactive updates
    }
  });
}

// Common deprecation patterns to watch for:
// - Renamed methods: client.oldMethod() -> client.newMethod()
// - Changed parameters: { key: 'x' } -> { apiKey: 'x' }
// - Removed features: Check release notes before upgrading
```

## Version Compatibility Matrix

| SDK Version | API Version | Node.js | Breaking Changes |
|-------------|-------------|---------|------------------|
| 3.x | 2024-01 | 18+ | Major refactor |
| 2.x | 2023-06 | 16+ | Auth changes |
| 1.x | 2022-01 | 14+ | Initial release |
