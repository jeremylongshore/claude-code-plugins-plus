# Primary-source notes

Research refreshed 2026-09-03. Re-open Snowflake documentation before an
operational decision because schemas, privileges, availability, and latency can
change.

- [DATA_QUALITY_MONITORING_EXPECTATION_STATUS](https://docs.snowflake.com/en/sql-reference/local/data_quality_monitoring_expectation_status)
  documents one row per expectation evaluation: false means satisfied, true means
  violated, and null means evaluation failure. The page does not publish a
  provider settlement SLA. An owner delay is only a declared assumption; absence
  and satisfied observations never prove present-tense quality health.
- [Information Schema DATA_METRIC_FUNCTION_REFERENCES](https://docs.snowflake.com/en/sql-reference/functions/data_metric_function_references)
  supplies selector-bound live association and notification configuration. Its
  visibility is privilege-filtered; zero rows do not mean disabled configuration.
- The selector-bound Information Schema expectation surface supplies current
  expectation definitions for one governed object. Snowflake's association
  reference identity binds the applied overload because the history surface does
  not expose a signature format compatible with the live surface.
- [Data-quality notifications](https://docs.snowflake.com/en/user-guide/data-quality-notifications)
  describes configuration, not proof that a notification was delivered.
- [Grouped DMF evaluation behavior](https://docs.snowflake.com/en/release-notes/2026/10_16)
  can collapse multiple group outcomes into one notification opportunity. The
  current receipt projection does not prove group-result completeness.

Usage history proves credit consumption, not the requirement denominator,
evaluation success, current definition, or notification delivery, and is not used
for a health classification.
