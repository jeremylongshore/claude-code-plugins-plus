# Primary-source notes

Research refreshed 2026-08-31. Re-open the live Snowflake documentation before
an operational decision; the links, columns, privileges, edition availability,
and latency boundaries can change.

- [Data quality introduction](https://docs.snowflake.com/en/user-guide/data-quality-intro) — system/custom data metric functions, expectations, anomaly detection, scheduling, and monitoring concepts.
- [DATA_QUALITY_MONITORING_EXPECTATION_STATUS](https://docs.snowflake.com/en/sql-reference/local/data_quality_monitoring_expectation_status) — one row per expectation evaluation, `EXPECTATION_VIOLATED` semantics, Enterprise Edition boundary, and required application roles.
- [DATA_QUALITY_MONITORING_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/data_quality_monitoring_usage_history) — usage attribution columns and Account Usage latency.
- [DATA_METRIC_FUNCTION_REFERENCES](https://docs.snowflake.com/en/sql-reference/account-usage/data_metric_function_references) — association inventory and schedule state.
- [Automatic sensitive-data classification](https://docs.snowflake.com/en/user-guide/classify-auto) — classification is a separate control and does not authorize collecting failed rows or customer values.

Design implications: a null expectation result can mean evaluation failure, not
pass; anomaly training is not health; usage proves consumption rather than
coverage; and a metric value without an approved objective cannot be called a
violation. The analyzer preserves all four distinctions.
