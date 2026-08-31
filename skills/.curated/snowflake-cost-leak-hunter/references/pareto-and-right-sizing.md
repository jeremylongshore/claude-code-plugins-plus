# Cost/latency tradeoffs and bounded right-sizing

Use this reference when an operator asks whether a cheaper warehouse or a size
change is justified. The analyzer's Pareto output compares supplied observations;
it is not a sizing oracle.

## Cost/latency Pareto

Group query-attribution rows by `query_parameterized_hash` (falling back to
`query_hash` only when parameterized hash is absent) and warehouse identity. For
each group retain query count, attributed compute credits, and average elapsed
time. A point is Pareto-efficient when no other supplied point is both no more
expensive and no slower, with one strict improvement. Different data windows,
cache state, warehouse behavior, or workload objectives make points incomparable;
keep them separate or label the comparison inconclusive.

## Right-sizing boundary

Only issue a review proposal when the operator supplies all of:

- current warehouse size and named warehouse identity;
- an explicit, finite candidate-size list and maximum size steps;
- an aligned baseline/measurement window and success criterion for latency,
  queueing, or cost;
- workload owner, Snowflake approver, and rollback size.

The analyzer never infers a candidate size, price, savings, or success threshold.
An approved experiment changes one variable and measures the same query hashes,
data window, cache/session context, concurrency, and source freshness. Stop if the
latency objective regresses, queueing or spill worsens, or cost cannot be
reconciled to a supplied rate-card/usage statement. No resize is executed by this
skill.

Primary sources:

- [Warehouse load history](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_load_history)
- [Exploring query execution](https://docs.snowflake.com/en/user-guide/performance-query-exploring)
