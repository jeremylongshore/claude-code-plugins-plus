# Warehouse and idle evidence collection

Use these read-only query shapes to build the normalized analyzer input. Replace bind
parameters through the approved client; do not concatenate untrusted identifiers into
SQL. Keep windows half-open: `>= start` and `< end`.

Primary sources:

- [WAREHOUSE_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history)
- [QUERY_ATTRIBUTION_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history)
- [Attributing cost](https://docs.snowflake.com/en/user-guide/cost-attributing)

## Warehouse metering

```sql
SELECT
  warehouse_id,
  warehouse_name,
  SUM(credits_used_compute) AS credits_used_compute,
  SUM(credits_attributed_compute_queries) AS credits_attributed_compute_queries,
  SUM(credits_used_cloud_services) AS credits_used_cloud_services,
  MAX(end_time) AS max_end_time
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= :window_start
  AND start_time < :window_end
GROUP BY warehouse_id, warehouse_name
ORDER BY credits_used_compute DESC;
```

Preserve NULL in `credits_attributed_compute_queries`. Do not translate it to zero.
Before combining accounts or reconciling with Organization Usage, set and record UTC as
required by the official view guidance.

Normalized row:

```json
{
  "warehouse_id": 12345,
  "warehouse_name": "TRANSFORM_WH",
  "credits_used_compute": "12.5",
  "credits_attributed_compute_queries": "8.75",
  "credits_used_cloud_services": "0.2"
}
```

## Query attribution by query

Keep query IDs and dimensions, but omit raw `QUERY_TEXT` from the evidence bundle by
default. SQL text can include literals and sensitive business data.

```sql
SELECT
  query_id,
  warehouse_id,
  warehouse_name,
  user_name,
  query_tag,
  query_parameterized_hash,
  credits_attributed_compute,
  COALESCE(credits_used_query_acceleration, 0)
    AS credits_used_query_acceleration,
  start_time,
  end_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY
WHERE start_time >= :window_start
  AND start_time < :window_end
ORDER BY credits_attributed_compute DESC;
```

Normalized row:

```json
{
  "query_id": "01abc...",
  "warehouse_name": "TRANSFORM_WH",
  "user_name": "SERVICE_USER",
  "query_tag": "team=data-platform",
  "credits_attributed_compute": "0.42",
  "credits_used_query_acceleration": "0"
}
```

Do not treat missing query rows as zero workload until the eight-hour view latency,
short-query exclusion, account scope, and Adaptive Warehouse limitation are considered.

## Attribution dimensions

Use dimensions already present in the evidence:

- Dedicated warehouse: warehouse tag or explicit owner mapping.
- Shared warehouse: user tag or approved identity mapping.
- Shared application: `QUERY_TAG` set by the application.
- Recurrent workload: `QUERY_PARAMETERIZED_HASH`, with query text withheld unless the
  operator explicitly approves it.

An empty tag is an attribution gap, not proof that usage lacks an owner.

## Serverless evidence

Serverless categories do not belong in `WAREHOUSE_METERING_HISTORY`, and resource
monitors do not govern them. Collect a service-specific approved usage view only after
verifying its availability, privilege, retention, unit, and latency on current official
documentation. Normalize each observed row as:

```json
{
  "service_type": "<official usage category>",
  "credits_used": "3.25",
  "source_view": "<fully qualified official view>"
}
```

Do not combine units. If a service reports tokens, bytes, or another unit rather than
credits, keep it outside this analyzer or convert only through an explicit documented
and user-approved model.

## Rate-card input

Currency conversion is optional. Supply only rates applicable to the evidence category:

```json
{
  "credit_rates": {
    "warehouse": {
      "unit_price": "<contract value>",
      "currency": "USD",
      "provenance": "customer rate card effective YYYY-MM-DD",
      "invoice_reconciled": false
    },
    "serverless:<official usage category>": {
      "unit_price": "<contract value>",
      "currency": "USD",
      "provenance": "customer rate card row identifier",
      "invoice_reconciled": false
    }
  }
}
```

The analyzer always labels these amounts estimated. A rate key that does not match a
usage category is not applied.

## Collection checks

- Query only the named window and columns.
- Record collection query IDs separately from workload query IDs.
- Record `CURRENT_ACCOUNT()`, `CURRENT_ROLE()`, and session timezone.
- Redact usernames if the intended audience does not need them.
- Do not export raw query text by default.
- Do not store CLI connection configuration or environment variables in the bundle.
- If a view fails, include the sanitized error and continue only with explicitly marked
  partial coverage.
