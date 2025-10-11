---
description: Detect and resolve database deadlocks
---

# Database Deadlock Detector

Identify and prevent database deadlocks.

## Deadlock Prevention

1. **Consistent Lock Order**: Always lock in same order
2. **Timeout Configuration**: Set lock timeouts
3. **Retry Logic**: Handle deadlock exceptions
4. **Minimize Transaction Time**: Quick operations

## Deadlock Detection (PostgreSQL)

```sql
-- Enable deadlock logging
SET log_lock_waits = on;
SET deadlock_timeout = '1s';

-- View locks
SELECT locktype, relation::regclass, mode, granted, pid
FROM pg_locks
WHERE NOT granted;
```

## When Invoked

Analyze deadlock patterns and provide solutions.
