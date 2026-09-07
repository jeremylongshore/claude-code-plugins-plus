# MergeTree Engines & Data Types Reference

Pick the right table engine and column types before you create your first
ClickHouse table. The `ORDER BY` key and engine choice determine how the table
merges, deduplicates, and pre-aggregates — they are hard to change later.

## MergeTree Engine Quick Reference

| Engine | Use Case |
|--------|----------|
| `MergeTree` | General-purpose analytics |
| `ReplacingMergeTree` | Upserts (dedup by ORDER BY key) |
| `SummingMergeTree` | Auto-sum numeric columns on merge |
| `AggregatingMergeTree` | Pre-aggregated materialized views |
| `CollapsingMergeTree` | State changes / versioned rows |

## Common Data Types

| Type | Example | Notes |
|------|---------|-------|
| `UInt8/16/32/64` | `user_id UInt64` | Unsigned integers |
| `Int8/16/32/64` | `delta Int32` | Signed integers |
| `Float32/64` | `price Float64` | IEEE 754 |
| `Decimal(P,S)` | `amount Decimal(18,2)` | Exact decimal |
| `String` | `name String` | Variable-length bytes |
| `DateTime` | `created_at DateTime` | Unix timestamp (seconds) |
| `DateTime64(3)` | `ts DateTime64(3)` | Millisecond precision |
| `UUID` | `id UUID` | 128-bit UUID |
| `Array(T)` | `tags Array(String)` | Variable-length array |
| `LowCardinality(T)` | `status LowCardinality(String)` | Dictionary encoding |
