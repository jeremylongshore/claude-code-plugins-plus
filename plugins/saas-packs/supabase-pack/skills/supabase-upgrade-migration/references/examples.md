## Examples

### Import Changes

```typescript
// Before (v1.x)
import { Client } from '@supabase/supabase-js';

// After (v2.x)
import { SupabaseClient } from '@supabase/supabase-js';
```

### Configuration Changes

```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new SupabaseClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure

```bash
npm install @supabase/supabase-js@1.x.x --save-exact
```

### Deprecation Handling

```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Supabase]', warning.message);
      // Log to tracking system for proactive updates
    }
  });
}

// Common deprecation patterns to watch for:
// - Renamed methods: client.oldMethod() -> client.newMethod()
// - Changed parameters: { key: 'x' } -> { apiKey: 'x' }
// - Removed features: Check release notes before upgrading
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
