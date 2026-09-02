# Operator statistics interpretation

Primary source:

- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)

Check the current source before a production decision. The function returns operator
statistics for completed queries executed within the documented past 14 days. The
caller needs `OPERATE` or `MONITOR` on the warehouse where the query ran.

## Collection

```sql
SELECT
  :query_id AS query_id,
  step_id,
  operator_id,
  parent_operators,
  operator_type,
  operator_statistics,
  execution_time_breakdown,
  operator_attributes
FROM TABLE(GET_QUERY_OPERATOR_STATS(:query_id))
ORDER BY step_id, operator_id;
```

`query_id` above is the validated selector repeated into every normalized row; do not
infer it later from a file name or surrounding report.

Do not retry with a more privileged role automatically. A privilege error becomes a
coverage limitation and an owner request.

## Normalized analyzer row

```json
{
  "query_id": "01abcdef-0123-4567-89ab-cdef01234567",
  "operator_id": 3,
  "operator_type": "Join",
  "operator_statistics": {
    "input_rows": 100,
    "output_rows": 250,
    "spilling": {
      "bytes_spilled_local_storage": 1024,
      "bytes_spilled_remote_storage": 4096
    },
    "pruning": {
      "partitions_scanned": 80,
      "partitions_total": 100
    }
  },
  "execution_time_breakdown": {
    "overall_percentage": 45.2
  },
  "operator_attributes": {
    "redacted": true
  }
}
```

Only include keys actually returned. Absence is unknown, not zero; the normalizer may
use zero only for a missing optional counter when no claim depends on its absence.

## Defensible observations

### Spill

`bytes_spilled_local_storage` and `bytes_spilled_remote_storage` are observed operator
counters. Remote spill is evidence that intermediate results exceeded memory and used
remote storage. It does not by itself prove the warehouse is undersized: query shape,
data volume, skew, and workload changes are competing explanations.

### Pruning

`partitions_scanned` and `partitions_total` support a scan fraction. A full scan can be
correct for a full-table workload. A low fraction can still be expensive if partitions
are large or the rest of the plan dominates. Do not prescribe clustering from this
ratio alone.

### Join expansion

For operators with nonzero input rows, `output_rows / input_rows` is a derived row
multiple. Snowflake's official example uses operator statistics to locate joins that
produce more rows than they consume. Expansion can still be valid many-to-many
semantics. Inspect approved redacted join conditions and business cardinality before
calling it a defect.

### Execution time breakdown

`overall_percentage` records the portion of query time associated with an operator.
Use it to rank investigation, not to set a universal severity threshold. Other
breakdown fields distinguish processing, synchronization, local disk I/O, remote disk
I/O, network communication, and initialization when present.

### I/O and cache

Bytes scanned, external bytes, network bytes, result bytes, and cache percentage are
observations. Cache conditions can make two otherwise similar executions incomparable.

## Evidence taxonomy

- `confirmed`: raw operator counter or time percentage supplied by the function.
- `estimated`: deterministic derived ratio such as output/input or scanned/total.
- `at-risk`: a causal hypothesis requiring workload context or comparison evidence.

Do not promote an estimated ratio or at-risk hypothesis to confirmed root cause.

## Unsupported or inconclusive cases

Stop operator-level diagnosis when:

- the query has not completed;
- it falls outside the documented retrieval window;
- warehouse privilege is missing;
- returned VARIANT objects are malformed or sanitized beyond interpretation;
- query plans or data conditions differ enough that the baseline is not comparable.
