# Snowflake Pitfall Source Matrix

Use this reference only when the audit reaches the corresponding pitfall. Snowflake
documentation defines platform behavior; the operator's account metadata, edition,
contract, policies, and workload measurements define the deployment decision.

| Topic | Official documentation | Supported conclusion | Verify in the account |
|---|---|---|---|
| Warehouse suspension and billing | [Warehouse overview](https://docs.snowflake.com/en/user-guide/warehouses-overview) | Warehouses use per-second billing with a minimum charge when started; auto-suspend avoids idle consumption. | Current size, state, suspend/resume properties, queueing, and resume latency. |
| Warehouse cost-control audit | [Cost-control checks](https://docs.snowflake.com/en/user-guide/cost-controlling-controls) | `SHOW WAREHOUSES` piped to a query is a documented way to find warehouses without an assigned monitor. | Whether an account-level monitor covers a warehouse and whether serverless usage exists. |
| Resource monitor scope | [Resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors) | Resource monitors govern warehouses, not serverless or AI features; threshold enforcement can occur after the precise quota. | Approved quota, action buffer, notification recipients, and supported budget coverage. |
| Least privilege | [Access-control considerations](https://docs.snowflake.com/en/user-guide/security-access-control-considerations) | Routine work should use scoped roles instead of broad administrative privileges. | Controlled elevation path, current grants, role ownership, and break-glass process. |
| Query evidence | [Query history table function](https://docs.snowflake.com/en/sql-reference/functions/query_history) | Session query history exposes query identifiers and execution metrics for bounded review. | Identical data, warehouse, cache conditions, and workload window before comparison. |
| Clustering | [Clustering keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys) and [`SYSTEM$CLUSTERING_INFORMATION`](https://docs.snowflake.com/en/sql-reference/functions/system_clustering_information) | Clustering is workload-dependent and maintenance consumes credits; clustering information supplies evidence. | Query selectivity, table size/micro-partitions, DML ratio, clustering depth, latency, and maintenance credits. |
| Deterministic loads | [`MERGE`](https://docs.snowflake.com/en/sql-reference/sql/merge) | Multiple matching source rows can make updates/deletes nondeterministic, and duplicate unmatched rows can duplicate inserts. | Stable business key, deterministic source precedence, target uniqueness, and replay result. |
| Stream staleness | [Managing streams](https://docs.snowflake.com/en/user-guide/streams-manage) and [stream introduction](https://docs.snowflake.com/en/user-guide/streams-intro) | A stream must be consumed before `STALE_AFTER`; stale streams can lose unconsumed change records. | `SHOW STREAMS` output, source retention, last consumption, replay source, and missing interval. |
| Load-file sizing | [Preparing data files](https://docs.snowflake.com/en/user-guide/data-load-considerations-prepare) | Approximately 100-250 MB compressed is Snowflake guidance for efficient parallel loading and Snowpipe queueing. | Actual compressed sizes, load duration, queueing, freshness, and producer constraints. |
| Recovery classes | [Temporary and transient tables](https://docs.snowflake.com/en/user-guide/tables-temp-transient) | Transient tables have no Fail-safe and at most one day of Time Travel. Permanent retention support depends on edition. | Table kind, retention, recovery objective, edition, owner, and authoritative replay source. |
| Account identifiers | [Account identifiers](https://docs.snowflake.com/en/user-guide/admin-account-identifier) | Organization-name/account-name identifiers are preferred; account locators remain supported. | Driver-specific identifier form and existing connection configuration. |
| Driver authentication | [Node.js authentication](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-authenticate) | The driver documents key-pair, OAuth, browser/identity-provider, and other authentication modes. | Organization-approved method, key/token lifecycle, file protection, network policy, and rotation. |

## Evidence Rules

- Prefer live `SHOW` output for immediate object state; note latency when using Account Usage.
- Do not infer currency cost from credits without the customer's contract rate.
- Do not infer supported retention, cross-region behavior, or governance limits from examples.
- Redact credentials, customer rows, account locators, staged object names, and sensitive
  object identifiers before evidence leaves the approved environment.
- When documentation and live behavior appear to conflict, stop the recommendation,
  capture the exact account/edition/context, and escalate through Snowflake support or the
  account owner rather than inventing an explanation.
