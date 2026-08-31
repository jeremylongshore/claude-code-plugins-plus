# Snowflake Architecture Source Matrix

Use this reference after requirements identify a candidate pattern. It records supported
platform primitives and the account-specific evidence required before architecture
approval; it is not a substitute for storage-owner, security-owner, or production-owner
authorization.

| Decision | Official documentation | Supported conclusion | Verify before selection |
|---|---|---|---|
| Warehouse behavior | [Warehouse overview](https://docs.snowflake.com/en/user-guide/warehouses-overview) | Separate warehouses isolate compute workloads; size and auto-suspend remain workload decisions. | Query concurrency, queueing, resume latency, credit baseline, monitor assignment, and recovery. |
| Iceberg catalog and storage | [Iceberg table creation](https://docs.snowflake.com/en/user-guide/tables-iceberg-create) | Snowflake supports Iceberg tables with Snowflake-managed storage or configured external volumes and catalogs. | Authoritative catalog, allowed writers, storage location, privileges, encryption, recovery, and engine compatibility. |
| External-volume trust | [External volumes](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume) | Customer-managed storage requires a configured and verified provider-specific trust relationship before table creation. | Storage-owner approval, least-privilege cloud identity, base URL, encryption, and access verification. Never copy credentials into the decision record. |
| Dynamic Iceberg output | [Dynamic Iceberg tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-tasks-create-iceberg) and [`CREATE DYNAMIC TABLE`](https://docs.snowflake.com/en/sql-reference/sql/create-dynamic-table) | Externally stored dynamic Iceberg output uses Snowflake as catalog; target lag is a target rather than a hard guarantee. | Supported account configuration, refresh history, warehouse, external volume, base location, failure recovery, and measured freshness. |
| Secure Data Sharing | [Secure Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro) | Shared objects remain provider-owned and are queried with consumer compute rather than copied into the consumer account. | Provider grants, consumer identifier, ownership, change compatibility, data policy, and revocation test. |
| Cross-region/cloud sharing | [Sharing across regions and cloud platforms](https://docs.snowflake.com/en/user-guide/secure-data-sharing-across-regions-platforms) | Cross-region or cross-cloud consumption can require replication and account/edition prerequisites. | Provider and consumer topology, replication configuration, supported edition, refresh behavior, credits, and recovery. |
| Secure views | [Secure views](https://docs.snowflake.com/en/user-guide/views-secure) | Secure views restrict definition visibility to authorized users and can reduce some inference risks, with performance and user-code caveats. | Consumer-role results, masking and row policies, small-group inference, identifiers, grant scope, and query profile. |
| Snowpark DataFrames | [Working with Snowpark DataFrames](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes) | DataFrame construction is lazy; actions such as `show`, `collect`, and writes evaluate the plan. | Query plan, pushdown, bounded actions, row/data minimization, runtime identity, warehouse, and failure behavior. |
| Python stored procedures | [Creating Python stored procedures](https://docs.snowflake.com/en/developer-guide/snowpark/python/creating-sprocs) | Stored-procedure registration has explicit package, stage, privilege, and runtime requirements; pinned packages improve repeatability. | Package policy and versions, stage ownership, handler inputs/outputs, owner/caller rights, logging, rollback, and redeployment. |
| Authentication | [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth), [OAuth](https://docs.snowflake.com/en/user-guide/oauth), and [workload identity federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation) | Snowflake documents non-password authentication options for different runtime and identity boundaries. | Organization-approved method, driver/runtime support, identity lifecycle, rotation, network policy, and secret storage. |

## Decision Evidence Rules

- Change one architectural variable at a time and compare against the same bounded baseline.
- Treat example object names, sizes, lag targets, and suspend settings as hypotheses, not
  recommendations or platform limits.
- Require the object owner to approve production DDL and the security/storage owner to
  approve cross-boundary trust.
- Record both the happy path and a failure/recovery test. Reject the pattern when rollback,
  entitlement revocation, catalog ownership, or authoritative replay cannot be demonstrated.
- Keep customer payloads, credentials, private-key material, cloud role secrets, and
  unredacted account identifiers out of the architecture record.
