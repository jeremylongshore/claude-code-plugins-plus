# Exploring System Tables

Once your table has data, ClickHouse's `system.*` tables let you inspect disk
usage, part counts, and merge behavior. This is the fastest way to confirm your
`PARTITION BY` and `ORDER BY` choices are producing sane on-disk layout.

## Check table size and row count

```typescript
// Check table size and row count
const stats = await client.query({
  query: `
    SELECT
      table,
      formatReadableSize(sum(bytes_on_disk)) AS disk_size,
      sum(rows) AS row_count,
      count() AS part_count
    FROM system.parts
    WHERE active AND database = currentDatabase() AND table = 'events'
    GROUP BY table
  `,
  format: 'JSONEachRow',
});
console.log('Table stats:', await stats.json());
```

**What the columns mean:**

- `disk_size` — compressed bytes on disk (ClickHouse compresses aggressively; a
  few rows may report a tiny size).
- `row_count` — total active rows across all parts.
- `part_count` — number of active parts. A freshly inserted table often has one
  part per insert batch; background merges collapse them over time. A high part
  count relative to rows means merges have not caught up yet.

## Useful follow-up system tables

| Table | What it tells you |
|-------|-------------------|
| `system.parts` | Per-part disk size, row count, partition, active flag |
| `system.columns` | Per-column compressed/uncompressed size |
| `system.merges` | In-progress background merges |
| `system.mutations` | Status of `ALTER ... UPDATE/DELETE` operations |
| `system.query_log` | History of executed queries + timing (if enabled) |
