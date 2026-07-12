# RocksDB State-Store Memory Tuning for Structured Streaming

A stateful Structured Streaming query keeps its running state — the aggregation
buckets, the join buffers, the `flatMapGroupsWithState` objects — in a **state
store** that survives across micro-batches. When that store is RocksDB, the state
lives in **native (off-heap) memory**, not the JVM heap. That one fact is why a
streaming job OOMs the driver or an executor while every heap metric you look at
reads healthy, and why the reflexive fix — raise `spark.executor.memory`, tune GC —
does nothing. The memory that killed the container was never on the heap to begin
with.

This reference covers the HDFS-backed vs RocksDB tradeoff, the config knobs that
**bound** RocksDB's native footprint, what **changelog checkpointing** changes about
the per-batch snapshot spike, how to read state size out of `StreamingQueryProgress`
instead of trusting heap dashboards, and the ordered fix list. Keys whose exact
spelling the author is unsure of are tagged _(verify)_ — pin those against the
release notes for your exact runtime before pasting them into a cluster config.

## Why RocksDB, and why off-heap

There are two state-store providers, selected by
`spark.sql.streaming.stateStore.providerClass`:

- **`HDFSBackedStateStoreProvider`** — the historical default. State lives in an
  in-memory map on the **JVM heap** of each executor, versioned to the checkpoint
  location (DBFS / cloud storage) as delta and snapshot files. It is fast and simple
  for small state, but the whole working set competes with your task memory for the
  same heap. At millions of keys / multi-GB state you get long GC pauses and, past
  the heap ceiling, an executor `OutOfMemoryError`. The state is bounded by
  `spark.executor.memory`, so the failure is at least honest — it shows up in heap
  metrics.
- **`RocksDBStateStoreProvider`** — an embedded RocksDB (native C++ LSM-tree)
  instance per state-store partition. State lives in RocksDB's **off-heap** memory —
  memtables (write buffers), a block cache for reads, and table-reader/index memory —
  and **spills to local disk** (`spark.local.dir` / `/local_disk0`) when it exceeds
  memory. Because it isn't on the heap and it can page to disk, RocksDB holds far
  larger state without GC pressure. Recent Databricks runtimes make it the **default**
  for stateful streaming _(verify the exact DBR that flipped the default for your
  runtime)_.

The trap is the second half of that tradeoff. RocksDB's memtables, block cache, and
open SST readers are all **native allocations the JVM never sees**. The Spark UI
Executors tab, GC logs, and heap-used dashboards report only on-heap usage — so they
stay flat and green while RocksDB's native arena grows batch over batch. What climbs
is the **container RSS** (process resident memory); when
`JVM heap + RocksDB native + OS overhead` exceeds physical RAM, the OS / cluster
manager kills the container. On Databricks the node is terminated with an
out-of-memory reason in the cluster event log while the heap never looked full.
**Heap metrics lie for RocksDB state — watch state size and container memory, not
heap.**

## Bounding the off-heap memory

By default each RocksDB instance manages its own memory, so a node running many
state-store partitions can allocate an unbounded sum of native memory. The fix is to
**bound the total** across all RocksDB instances on a node and let them share one
budget:

```text
# Bound total RocksDB native memory across all state-store instances on a node
spark.sql.streaming.stateStore.rocksdb.boundedMemoryUsage    true
spark.sql.streaming.stateStore.rocksdb.maxMemoryUsageMB      2000     # the shared cap
spark.sql.streaming.stateStore.rocksdb.writeBufferCacheRatio 0.5      # share for memtables
spark.sql.streaming.stateStore.rocksdb.highPriorityPoolRatio 0.1      # share for index/filter blocks
```

When `boundedMemoryUsage` is `true`, all instances on the node share one LRU cache
sized to `maxMemoryUsageMB`; `writeBufferCacheRatio` carves out the slice reserved
for write buffers and `highPriorityPoolRatio` the slice kept for high-priority
(index/filter) blocks. Databricks also exposes an umbrella toggle,
`spark.databricks.streaming.statefulOperator.stateRocksDBBoundedMemoryUsage` _(verify
the exact key against your DBR release notes)_ — set it `true` to enable the bounded
model without hand-setting the OSS keys.

The critical sizing rule: **`maxMemoryUsageMB` is a budget you must fund from
physical RAM the JVM heap does not already own.** On a node,
`spark.executor.memory` (heap) + `maxMemoryUsageMB` (RocksDB) + OS/overhead must fit
in physical memory with headroom — setting the cap without shrinking the heap just
relocates the OOM. The per-instance knobs
(`writeBufferSizeMB`, `maxWriteBufferNumber`, `blockSizeKB`) still let you trade
memory for compaction frequency, but the bounded cap is the one that actually keeps
the node from being killed.

## Changelog checkpointing

Without changelog checkpointing, RocksDB persists durability by taking a **full
snapshot** of the instance at (or near) every micro-batch commit and uploading it to
the checkpoint location. That snapshot has to be materialized and synced on the task
commit path — it forces flush/compaction work and an upload that both **spike memory
and stall the batch**, and the spike scales with total state size. Long, sawtooth
batch durations on a large-state query are the classic signature.

Changelog checkpointing changes the unit of durability. With
`spark.sql.streaming.stateStore.rocksdb.changelogCheckpointing.enabled = true`, each
micro-batch uploads only a **changelog** — the delta of state mutations since the last
commit — while **full snapshots move to a background thread** on a periodic cadence
(governed by the snapshot interval,
`spark.sql.streaming.stateStore.minDeltasForSnapshot` _(verify this key governs
RocksDB changelog snapshotting in your runtime)_). Because the commit path now writes
a small delta instead of forcing a full snapshot + upload, the **per-batch memory and
latency spike drops sharply** and batch durations flatten. The tradeoff is recovery:
restart replays the changelog on top of the most recent background snapshot, so a long
changelog tail lengthens recovery — exactly what the snapshot interval tunes. Recent
Databricks runtimes enable it by default _(verify the DBR that made it default)_; on
older runtimes it is usually the single biggest latency win for a large-state query.

## Diagnosing — read state size, not heap

The authoritative signal is `StreamingQueryProgress`, delivered per batch via a
`StreamingQueryListener.onQueryProgress` callback (or `query.lastProgress` /
`query.recentProgress`). Its `stateOperators` array carries one entry per stateful
operator, and those fields — not heap dashboards — tell you whether state is the
problem:

- **`numRowsTotal`** — total rows currently held in state for the operator. If this
  climbs monotonically batch over batch, state is not being expired, and RocksDB
  native memory grows with it. This is the leading indicator of a state-driven OOM.
- **`memoryUsedBytes`** — memory the state store reports as in use. For RocksDB this
  reflects the native arena, so it climbs while heap stays flat — the direct
  refutation of a healthy-heap dashboard.
- **`numRowsUpdated` / `numRowsRemoved`** — churn. Many updates with near-zero
  removals means nothing is aging out (missing or too-loose watermark / TTL).
- **`numRowsDroppedByWatermark`** — late rows the watermark discarded. Zero here on a
  growing-state query is a hint the watermark is too loose to bound the state.
- **`customMetrics`** — RocksDB counters such as `rocksdbTotalBytesRead` /
  `rocksdbTotalBytesWritten`, `rocksdbGetLatency` / `rocksdbPutLatency`,
  `rocksdbReadBlockCacheHitCount` / `rocksdbReadBlockCacheMissCount`,
  `rocksdbWriterStallLatencyMs`, and native-memory breakdowns like
  `rocksdbPinnedBlocksMemoryUsage` _(verify exact names against your DBR)_. Rising
  writer-stall latency and a collapsing block-cache hit rate mean the working set no
  longer fits the cache and RocksDB is thrashing disk.

```python
# Correlate state growth to memory — this, not the heap graph, diagnoses the OOM
from pyspark.sql.streaming import StreamingQueryListener


class StateWatch(StreamingQueryListener):
    def onQueryStarted(self, event): pass

    def onQueryProgress(self, event):
        for op in event.progress.stateOperators:
            print(op.numRowsTotal, op.memoryUsedBytes, op.numRowsDroppedByWatermark)

    def onQueryTerminated(self, event): pass


spark.streams.addListener(StateWatch())
```

**The correlation that names the root cause:** a driver or executor OOM lands while
`numRowsTotal` and `memoryUsedBytes` trend up across recent progress rows and the JVM
heap is flat. That pattern is state size, not heap — and no amount of heap or GC
tuning touches it.

## The fixes, in order

Apply in sequence — the first two are config, the third is query logic, the fourth is
capacity:

1. **Bound the native memory.** Enable `boundedMemoryUsage` and set `maxMemoryUsageMB`
   to a budget funded from physical RAM outside the JVM heap (see the sizing rule
   above). This converts an unbounded native leak into a fixed, disk-spilling cap.
2. **Enable changelog checkpointing.** Set
   `...rocksdb.changelogCheckpointing.enabled = true` to kill the per-batch full-
   snapshot spike and flatten batch latency.
3. **Size the state — expire old keys.** Memory is a function of how many keys you
   retain. Bound retention so state does not grow forever:

   ```python
   # Windowed aggregations / stream-stream joins: a watermark drops state past the bound
   from pyspark.sql.functions import window

   agg = (events
          .withWatermark("event_time", "10 minutes")
          .groupBy(window("event_time", "5 minutes"), "key")
          .count())
   ```

   For arbitrary stateful operators, set explicit timeouts: `flatMapGroupsWithState`
   with `GroupStateTimeout.EventTimeTimeout` plus `state.setTimeoutTimestamp(...)`, or
   the newer `transformWithState` API's per-value **TTL** on `ValueState` / `ListState`
   / `MapState` _(verify the DBR / Spark version that ships `transformWithState` TTL)_.
   A too-loose or missing watermark is the most common reason `numRowsTotal` never
   stops climbing.
4. **Pick the instance type for off-heap headroom.** Choose memory-optimized nodes
   sized so `executor heap + maxMemoryUsageMB + overhead < physical RAM`, and prefer
   **fast local NVMe SSD** (`/local_disk0`) — RocksDB spills, compacts, and reads
   against local disk, so slow storage surfaces as writer stalls and cache misses in
   the custom metrics. Raising only `spark.executor.memory` grows the heap, not the
   native budget RocksDB spends, so it never fixes a RocksDB OOM.

## Configuration reference

| Key | What it does | Recommended |
| --- | --- | --- |
| `spark.sql.streaming.stateStore.providerClass` | Selects RocksDB vs HDFS-backed provider | `...state.RocksDBStateStoreProvider` for large state (default on recent DBR) |
| `spark.sql.streaming.stateStore.rocksdb.boundedMemoryUsage` | Caps total native memory across all RocksDB instances on a node | `true` |
| `spark.sql.streaming.stateStore.rocksdb.maxMemoryUsageMB` | The shared cap in MB when bounded | Size to node RAM minus heap and overhead (default `500`) |
| `spark.sql.streaming.stateStore.rocksdb.writeBufferCacheRatio` | Share of the cap reserved for write buffers / memtables | `0.5` default — tune per workload _(verify)_ |
| `spark.sql.streaming.stateStore.rocksdb.highPriorityPoolRatio` | Share of block cache for high-priority index/filter blocks | `0.1` default _(verify)_ |
| `spark.databricks.streaming.statefulOperator.stateRocksDBBoundedMemoryUsage` | Databricks umbrella toggle for the bounded-memory model | `true` _(verify exact key)_ |
| `spark.sql.streaming.stateStore.rocksdb.changelogCheckpointing.enabled` | Upload per-batch deltas + async background snapshots instead of a full snapshot each batch | `true` |
| `spark.sql.streaming.stateStore.minDeltasForSnapshot` | Delta/changelog files before a snapshot is taken | Default `10`; raise to cut snapshot frequency (lengthens recovery) _(verify applies to RocksDB changelog)_ |
| `spark.sql.streaming.stateStore.rocksdb.writeBufferSizeMB` | Size of a single memtable | Lower to reduce per-instance memory _(verify default)_ |
| `spark.sql.streaming.stateStore.rocksdb.maxWriteBufferNumber` | Number of memtables before a forced flush | Keep low to bound memory _(verify default)_ |
| `spark.sql.streaming.stateStore.rocksdb.blockSizeKB` | SST block size for the read path | Default is fine for most workloads |
| `spark.sql.streaming.stateStore.rocksdb.trackTotalNumberOfRows` | Populates `numRowsTotal` in progress (small overhead) | `true` while diagnosing; consider `false` once tuned |

## Version-accuracy anchors

- **RocksDB is off-heap; HDFS-backed is on-heap** — the load-bearing distinction. A
  plan that fixes a RocksDB OOM with heap/GC tuning has misdiagnosed the provider.
- **The bounded cap `maxMemoryUsageMB` must be funded outside the JVM heap.** Set
  without shrinking the heap or growing the node, it just moves the OOM off-heap.
- **Changelog checkpointing uploads deltas, not full snapshots**, and pushes snapshots
  to a background cadence — a checkpoint-shape change, not a correctness change, and
  the reason it removes the per-batch spike.
- **State size (`numRowsTotal` / `memoryUsedBytes`), not heap, is the diagnostic** — a
  monotonic climb with a flat heap is the fingerprint of missing watermark/TTL.

Exact defaults, per-runtime metric names, and whether a given key ships drift across
DBR / OSS Spark versions — _(verify each against the state-store docs for your exact
runtime before applying)_.

## Sources

- Apache Spark — _Structured Streaming Programming Guide_, "RocksDB State Store
  Implementation" (provider class, changelog checkpointing, `rocksdb.*` configs,
  bounded-memory keys), spark.apache.org `/docs/latest/structured-streaming-programming-guide.html`.
- Databricks — _Configure RocksDB state store on Databricks_ / _Structured Streaming
  state management_ (RocksDB as default for large state, bounded-memory guidance,
  changelog checkpointing defaults), docs.databricks.com `/structured-streaming/rocksdb-state-store`.
- Apache Spark — `StreamingQueryProgress` / `StateOperatorProgress` API
  (`numRowsTotal`, `memoryUsedBytes`, `numRowsDroppedByWatermark`, `customMetrics`),
  spark.apache.org Scala/Python streaming API docs.
- Databricks Engineering blog — _Faster stateful stream processing with changelog
  checkpointing / async state_ (why full-snapshot commits spike latency and memory),
  databricks.com/blog.
- Apache Spark JIRA — SPARK-40876 (changelog checkpointing) and the RocksDB
  bounded-memory work, for the design intent behind the `rocksdb.*` bounded-memory and
  changelog keys, issues.apache.org/jira.
