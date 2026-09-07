# ClickHouse Data Handling — Worked Examples

End-to-end scenarios that chain the individual steps from
[implementation.md](implementation.md) into complete, auditable workflows.

## Example 1: Fulfilling a GDPR "right to erasure" request

A user (user_id 42) submits an erasure request. The compliant flow is
export-then-delete-then-log so the request is provable after the fact.

```sql
-- 1. Confirm what data exists for the subject (scope the request)
SELECT partition, count() AS rows
FROM system.parts
WHERE database = 'analytics' AND table = 'events' AND active
GROUP BY partition;

-- 2. Delete across every table holding the subject's rows (mutation-based,
--    verifiable — the compliant path, not lightweight DELETE)
ALTER TABLE analytics.events   DELETE WHERE user_id = 42;
ALTER TABLE analytics.sessions DELETE WHERE user_id = 42;

-- 3. Verify the mutations completed before reporting the request as fulfilled
SELECT table, mutation_id, is_done, parts_to_do
FROM system.mutations
WHERE database = 'analytics' AND command LIKE '%user_id = 42%'
ORDER BY create_time DESC;

-- 4. Write an immutable audit record (this row has NO TTL and is never deleted)
INSERT INTO analytics.audit_log (action, actor, target, details)
VALUES ('DELETE_ALL', 'privacy-service', 'user:42',
        '{"reason":"gdpr_erasure","request_id":"DSAR-2026-0042"}');
```

Run the full delete + audit-log insert through the TypeScript `deleteUserData`
helper in [implementation.md](implementation.md) Step 4 when the request comes
from an application rather than a console.

## Example 2: Standing up a retention-safe events table from scratch

```sql
-- Hot/cold/delete tiering plus PII column-TTL in one table definition
CREATE TABLE analytics.events (
    event_id    UUID DEFAULT generateUUIDv4(),
    event_type  LowCardinality(String),
    user_id     UInt64,
    email       String,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (event_type, created_at)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 7   DAY TO VOLUME 'hot',
    created_at + INTERVAL 30  DAY TO VOLUME 'cold',
    created_at + INTERVAL 365 DAY DELETE,
    -- null out the raw email at 30 days but keep the analytics row
    created_at + INTERVAL 30  DAY RECOMPRESS CODEC(ZSTD(1));

ALTER TABLE analytics.events
    MODIFY COLUMN email String DEFAULT ''
    TTL created_at + INTERVAL 30 DAY;
```

## Example 3: Auditing which tables are missing a retention policy

```sql
-- Any MergeTree table in the analytics DB with no TTL is a compliance gap
SELECT database, name AS table, engine
FROM system.tables
WHERE database = 'analytics'
  AND engine LIKE '%MergeTree%'
  AND result_ttl_expression = '';
```

Feed the result into a review: business-metric tables may legitimately omit TTL,
but any table holding PII that appears here needs a column-TTL or masking view
added (see [implementation.md](implementation.md) Steps 1 and 3).
