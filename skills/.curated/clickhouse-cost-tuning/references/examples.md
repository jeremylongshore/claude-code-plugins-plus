# ClickHouse Cost Tuning — Worked Examples

End-to-end scenarios that combine the queries in
[implementation.md](implementation.md) into a decision → action → verification loop.

## Example 1: Storage bill doubled month-over-month

**Situation:** the storage line on the ClickHouse Cloud invoice jumped from 40 GB
to 90 GB with no new tables added.

1. Run the "Storage cost breakdown by table" query (Step 2). One table,
   `analytics.events`, holds 70 GB compressed.
2. Run the "Storage by column" query. The `properties` JSON column is 55 GB with a
   compression ratio of only 2.1 — poorly compressed text.
3. Apply a better codec and re-merge (Step 3):

   ```sql
   ALTER TABLE analytics.events MODIFY COLUMN properties String CODEC(ZSTD(3));
   OPTIMIZE TABLE analytics.events FINAL;
   ```

4. Re-run the column query. `properties` now compresses at 6.8, dropping the table
   from 70 GB to ~28 GB. **Result: storage bill back under the previous baseline.**

## Example 2: Compute cost is the real driver

**Situation:** storage is cheap but the compute line dominates the bill.

1. Run the "most expensive queries" query (Step 6). One dashboard query does a full
   `count()` over `events` every 30 seconds — billions of rows scanned per hour.
2. Replace it with a materialized view so the dashboard reads a tiny pre-aggregated
   table instead of scanning raw events (Step 6).
3. Enable idle suspension and auto-scaling in the Cloud Console so replicas spin
   down between bursts (Step 5). **Result: compute hours fall sharply because the
   hot-path query no longer scans the base table and idle replicas suspend.**

## Example 3: Old data you never query is still billed

**Situation:** you keep 3 years of events but dashboards only touch the last 90 days.

1. Add a tiered TTL so recent data stays hot, older data moves to cheap cold
   storage, and very old data is deleted (Step 4):

   ```sql
   ALTER TABLE analytics.events
       MODIFY TTL
           created_at + INTERVAL 30 DAY TO VOLUME 'hot',
           created_at + INTERVAL 90 DAY TO VOLUME 'cold',
           created_at + INTERVAL 365 DAY DELETE;
   ```

2. For an immediate one-time reclaim, drop whole partitions rather than waiting for
   TTL merges:

   ```sql
   ALTER TABLE analytics.events DROP PARTITION '202401';
   ```

   **Result: storage footprint drops immediately and stays bounded going forward.**
