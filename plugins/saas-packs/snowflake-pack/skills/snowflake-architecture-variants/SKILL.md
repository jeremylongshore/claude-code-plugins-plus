---
name: snowflake-architecture-variants
description: 'Choose and implement Snowflake architecture blueprints: data lakehouse,
  data mesh,

  data sharing, and Snowpark-native patterns for different scales.

  Use when designing Snowflake data platforms, choosing between architectures,

  or implementing data sharing and Snowpark patterns.

  Trigger with phrases like "snowflake architecture", "snowflake lakehouse",

  "snowflake data mesh", "snowflake data sharing", "snowflake Snowpark".

  '
allowed-tools: Read, Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- data-warehouse
- analytics
- snowflake
compatibility: Designed for Claude Code
---
# Snowflake Architecture Variants

## Overview

Choose among four composable patterns: a centralized warehouse, Iceberg tables, domain
ownership with secure data sharing, and Snowpark processing. These are decision patterns,
not fixed deployment sizes; select from ownership, interoperability, recovery, security,
and measured workload requirements rather than team-count or terabyte thresholds.

## Prerequisites

- Read-only access to the current architecture, SQL, grants, and deployment configuration.
- Workload evidence: data sources, freshness objective, concurrency, query profile,
  recovery requirement, and measured credit usage.
- Account edition, regions, cloud platforms, allowed authentication methods, and data
  classification policy.
- Named owners for storage, schemas, shares, and compute. Production DDL requires explicit
  owner approval and a tested rollback or parallel-run plan.

Use `Read` to inspect the actual design and `Grep` to locate storage integrations, external
volumes, shares, secure views, Snowpark registrations, embedded credentials, and local data
collection. Never copy secrets or customer payloads into the architecture record.

## Instructions

1. Define the boundary: producers, consumers, data classifications, regions, recovery
   targets, and who owns schema compatibility.
2. Establish a measured baseline for latency, concurrency, freshness, and credits. Keep
   currency conversion separate and use only the customer's contract rate.
3. Select the simplest pattern that satisfies the hard requirements. Combine patterns
   only where the boundary is explicit, such as central ingestion with domain-owned views.
4. Prototype with non-sensitive data and production-like query shapes. Change one design
   variable at a time and record the result.
5. Validate grants, recovery, failure behavior, and cost controls. Promote only after the
   acceptance criteria pass; otherwise roll back to the previous path.

## Variant A: Centralized Data Warehouse

**Use when:** one platform owner can govern ingestion, transformation, semantic models,
and access, and consumers do not require an open table format.

```sql
CREATE DATABASE DW;
CREATE SCHEMA DW.RAW;
CREATE SCHEMA DW.CURATED;
CREATE SCHEMA DW.ANALYTICS;

CREATE WAREHOUSE ETL_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;

CREATE WAREHOUSE QUERY_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;
```

The sizes and suspend values are starting hypotheses, not recommendations. Test them with
representative ingestion and query concurrency, then retain or revert based on explicit
queueing, latency, and credit criteria. Separate warehouses can isolate workloads but add
governance and cost-control responsibilities.

## Variant B: Iceberg Tables

**Use when:** open-format interoperability or existing Iceberg data is a hard requirement.
Choose deliberately between Snowflake as the Iceberg catalog and an externally managed
catalog. Storage and catalog ownership determine which systems may write safely.

For a Snowflake-managed proof of concept, a running warehouse and sufficient privileges
are prerequisites:

```sql
CREATE ICEBERG TABLE ANALYTICS.EVENTS_ICEBERG (
  event_id STRING,
  event_type STRING,
  event_timestamp TIMESTAMP_NTZ
)
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
  BASE_LOCATION = 'analytics/events/';
```

For customer-managed object storage, an administrator must create and verify the external
volume before the table. The provider-specific trust relationship and storage permissions
belong in the cloud security workflow; do not invent role ARNs or embed cloud credentials.

An externally stored dynamic Iceberg table can materialize transformations when Snowflake
is the catalog:

```sql
CREATE DYNAMIC ICEBERG TABLE ANALYTICS.CURATED_EVENTS
  TARGET_LAG = '30 minutes'
  WAREHOUSE = ETL_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'ANALYTICS_VOLUME'
  BASE_LOCATION = 'curated/events/'
AS
  SELECT event_id, event_type, event_timestamp
  FROM ANALYTICS.EVENTS_ICEBERG
  WHERE event_type IS NOT NULL;
```

`TARGET_LAG` is a scheduling target, not a hard service-level guarantee. Validate actual
refresh history and failure recovery. Dynamic Iceberg output must use Snowflake as the
catalog; do not present an externally managed catalog as a supported output configuration.

## Variant C: Domain Ownership with Secure Data Sharing

**Use when:** domains need independent ownership or accounts while consumers need governed,
read-only access. Secure Data Sharing avoids copying shared data into the consumer account;
consumers use their own compute. Cross-region and cross-cloud consumption can require
replication and account/edition prerequisites, so verify topology before promising access.

```sql
-- Provider account
CREATE SHARE FINANCE_SHARE;
GRANT USAGE ON DATABASE FINANCE_DW TO SHARE FINANCE_SHARE;
GRANT USAGE ON SCHEMA FINANCE_DW.GOLD TO SHARE FINANCE_SHARE;

CREATE SECURE VIEW FINANCE_DW.GOLD.REVENUE_SUMMARY AS
  SELECT region,
         product_line,
         SUM(revenue) AS total_revenue,
         COUNT(DISTINCT customer_id) AS customer_count
  FROM FINANCE_DW.SILVER.TRANSACTIONS
  GROUP BY region, product_line;

GRANT SELECT ON VIEW FINANCE_DW.GOLD.REVENUE_SUMMARY TO SHARE FINANCE_SHARE;
ALTER SHARE FINANCE_SHARE ADD ACCOUNTS = ORG_NAME.CONSUMER_ACCOUNT;

-- Consumer account
CREATE DATABASE FINANCE_SHARED
  FROM SHARE ORG_NAME.PROVIDER_ACCOUNT.FINANCE_SHARE;
```

Secure views limit definition visibility to authorized roles and can reduce some inference
risks, but they are not a blanket exfiltration control. Review row-access and masking
policies, aggregation leakage, consumer entitlements, and secure-view performance. Do not
put direct identifiers into shared aggregates unless policy explicitly permits it.

## Variant D: Snowpark Processing

**Use when:** DataFrame transformations or governed Python execution should remain close
to Snowflake data. Establish the `Session` through an administrator-approved connection
profile or workload identity using documented key-pair, OAuth, or workload-identity
authentication. Do not place passwords, tokens, or private keys in code.

```python
from snowflake.snowpark.functions import avg, col, current_date, dateadd, lit, sum as sf_sum

# `session` is supplied by the authenticated runtime.
orders = session.table("DW.CURATED.ORDERS")
revenue = (
    orders
    .filter(col("ORDER_DATE") >= dateadd("day", lit(-90), current_date()))
    .group_by("CUSTOMER_ID")
    .agg(
        sf_sum("AMOUNT").alias("TOTAL_SPEND"),
        avg("AMOUNT").alias("AVG_ORDER"),
    )
    .filter(col("TOTAL_SPEND") > 1000)
    .sort(col("TOTAL_SPEND").desc())
)

# DataFrame construction is lazy. This action executes the plan in Snowflake.
revenue.show()
```

Keep large data in Snowflake rather than collecting it locally. Stored procedures and UDFs
require separate registration, stage, package, privilege, and runtime decisions; pin
package versions for repeatable production registration. Do not present an in-memory model
or undefined object as a deployable UDF.

## Decision Matrix

| Decision factor | Centralized warehouse | Iceberg | Domain sharing | Snowpark |
|---|---|---|---|---|
| Primary owner | Platform team | Storage/catalog owner | Producing domain | Application/data team |
| Strongest fit | Governed SQL analytics | Open-format interoperability | Read-only cross-boundary products | Pushdown Python/DataFrames |
| Storage/catalog | Snowflake native | Explicit Iceberg catalog and volume | Provider-owned objects | Existing Snowflake objects |
| Consumer boundary | Roles within an account | Engines allowed by catalog policy | Shares/listings across approved accounts | Authenticated runtime/session |
| Key risk | Central bottleneck | Split-brain writers or storage trust | Entitlement and inference leakage | Local collection or unsafe packages |
| Proof required | Concurrency and recovery test | Catalog/write ownership test | Grant, region, and policy test | Pushdown, package, and auth test |

## Error Handling

| Condition | Response |
|---|---|
| External volume cannot be verified | Stop table creation; have the storage owner validate trust and least-privilege access. |
| Iceberg catalog or writer ownership is ambiguous | Stop all writers and designate one authoritative catalog/write path before migration. |
| Share is inaccessible | Verify provider grants, consumer account identifier, region/cloud prerequisites, and database-from-share privilege. |
| Secure view exposes sensitive groups | Revoke the share grant, review masking/row policies and aggregation thresholds, then retest with a consumer role. |
| Snowpark plan collects large data locally | Replace collection with pushdown transformations or bounded sampling; do not log rows. |
| Prototype misses acceptance criteria | Revert the single changed variable and retain the previous production path. |

## Output

Produce an architecture decision record containing:

- current state, hard requirements, owners, regions, data classifications, and evidence;
- selected pattern and rejected alternatives with measurable reasons;
- object and trust boundaries, authentication method, least-privilege roles, and data
  minimization controls;
- a prototype plan with one-variable changes, acceptance thresholds, and observed results;
- rollout, monitoring, failure recovery, and rollback steps; and
- open assumptions clearly marked rather than converted into platform claims.

Exclude passwords, tokens, private-key material, cloud role credentials, customer payloads,
and unredacted account identifiers.

## Examples

**Open-format requirement:** the data lake already has a designated Iceberg catalog and
multiple approved readers. Compare externally managed and Snowflake-catalog tables, verify
one authoritative writer path, test schema evolution and recovery, and choose only after
the storage owner approves the trust relationship.

**Cross-account product:** finance owns a summarized revenue view and two consumer accounts
need read-only access. Validate region/cloud topology, apply masking or row policies before
the share grant, test through a consumer role, and roll back by revoking the grant if the
entitlement or aggregation-leakage test fails.

**Python transformation:** a DataFrame pipeline currently downloads a large table. Rewrite
one operation for Snowpark pushdown, compare plan, latency, and credits on the same bounded
dataset, and retain the change only if it meets the approved criteria without local row
collection.

## References

Read [the official-source matrix](references/official-sources.md) when selecting a pattern
or validating storage, catalog, sharing, authentication, runtime, or regional prerequisites.
It separates documented platform behavior from deployment-specific decisions that require
account evidence and owner approval.
