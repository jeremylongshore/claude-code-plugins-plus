---
name: snowflake-common-errors
description: 'Diagnose and fix common Snowflake errors and SQL compilation failures.

  Use when encountering Snowflake error codes, failed queries,

  authentication issues, or warehouse/connection problems.

  Trigger with phrases like "snowflake error", "fix snowflake",

  "snowflake not working", "snowflake SQL error", "snowflake 002003".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(snow connection test:*)
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
# Snowflake Common Errors

## Overview

Diagnose Snowflake failures from the exact error, query or login identifier, client
context, and current Snowflake evidence. Error numbers and message fragments can
overlap across features; do not apply a change from the number alone.

Use **Read** and **Grep** on sanitized client logs and configuration. Use
`Bash(curl:*)` only for a URL returned by Snowflake's current connectivity workflow
or an operator-approved Snowflake status endpoint. Never construct a diagnostic URL
from an untrusted environment value or use an undocumented authentication endpoint.

## Prerequisites

- Exact sanitized error code, SQLSTATE, message, timestamp, client/driver name and
  version, and query ID or login-failure UUID when present.
- An approved client profile using the production authentication method; do not
  use literal test passwords or print credentials and environment variables.
- A least-privileged diagnostic role authorized to view the affected objects,
  warehouse, query history, or login details required for the case.
- The expected account identifier, user login name, role, database, schema, and
  warehouse from an approved configuration source.
- Change approval before grants, key rotation, parameter changes, warehouse
  changes, query cancellation, or any other state mutation.

## Instructions

### Step 1: Preserve the failure evidence

Record the exact error and identifiers before retrying. Redact SQL literals,
bind values, object names when required, account identifiers, IP addresses, and
authentication material according to the incident policy. Preserve timestamps in
UTC and identify the host or workload that observed the error.

### Step 2: Classify the failing layer

Choose the first matching boundary:

1. **Connectivity** — DNS, TLS, proxy, OCSP, or required stage endpoint failure.
2. **Authentication** — rejected password, federated identity, OAuth, programmatic
   token, or key-pair JWT.
3. **Session context** — missing or wrong role, database, schema, or warehouse.
4. **Authorization/object resolution** — object is absent, misqualified, case-
   sensitive, or hidden by missing privileges.
5. **Compilation** — SQL syntax, identifier, function, or templating failure.
6. **Execution/resource** — cancellation, timeout, queueing, spilling, or retry.
7. **Result consumption** — client memory, network path, or fetch behavior.

Do not rotate credentials for a DNS failure, grant privileges for a syntax error,
or resize compute before the query profile and history support that diagnosis.

### Step 3: Establish session context with read-only SQL

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_USER(), CURRENT_ROLE(),
       CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE();
```

Compare the result to the approved workload configuration. A `NULL` database,
schema, or warehouse can be valid for statements that do not require it; correct
only the context required by the failed statement.

### Step 4: Use the right history surface

For live triage, use an Information Schema `QUERY_HISTORY` table function with a
bounded time range and result limit. It covers recent activity and applies function
arguments before a later `WHERE` clause. Use the Account Usage `QUERY_HISTORY` view
for longer retention and broader analysis, but account for its documented latency
of up to 45 minutes. Do not interpret a missing fresh row there as proof that a
query never ran.

Select identifiers, status, timing, context, and error columns by default. Avoid
selecting `query_text` or `bind_values` into a shared incident artifact unless the
review explicitly requires and protects them.

### Step 5: Apply the smallest evidence-backed correction

- **Object does not exist or not authorized / 002003:** verify the fully qualified
  name, quoted-identifier case, active role, object existence, and grants. Do not
  grant access automatically; route a required grant to the object owner.
- **No active warehouse:** verify that the statement needs compute, the intended
  warehouse exists, and the role has `USAGE`. Select the approved warehouse; do
  not assume auto-resume or switch to unrelated compute.
- **SQL compilation / 001003:** inspect the reported line and position against the
  exact submitted SQL. Do not rewrite valid syntax from memory. Snowflake accepts
  both quoted and unquoted date-part arguments in documented date/time examples.
- **JWT token is invalid / 390144:** preserve the UUID, have an authorized
  administrator retrieve its login-failure details, then compare account/user
  claims, `LOGIN_NAME`, clock, algorithm, and public-key fingerprint. Do not
  regenerate or replace keys before identifying the mismatch and planning rotation.
- **Connectivity:** use `snow connection test` or the Snowflake Connector for
  Python diagnostic feature and the URLs returned by Snowflake's allowlist
  workflow. Do not invent a health-check or authentication URL.
- **Large result/client memory:** reduce projected data where appropriate or use
  the official Node.js streaming and Python `fetchmany()` patterns. Do not treat a
  client out-of-memory failure as proof the warehouse is undersized.
- **Timeout or slow query:** inspect the query profile, queueing, bytes scanned,
  spills, retry cause, and configured timeout hierarchy before changing parameters
  or warehouse size. Any higher timeout is an approved operational choice, not a
  universal fix.

Detailed read-only queries and connector examples are in
[the diagnostic reference](references/diagnostic-reference.md).

### Step 6: Verify and close

Repeat the smallest safe reproduction with the same role and context. Require a
new query ID or client receipt, the expected result, and no new authorization or
data-integrity regression. Record the correction, evidence, owner, and rollback or
reversal procedure. If the result conflicts with the hypothesis, revert the change
where applicable and return to classification.

## Output

Produce a diagnostic record containing:

- sanitized error, SQLSTATE, query ID/login UUID, timestamps, and client version;
- expected versus observed account, role, namespace, warehouse, and auth method;
- classified failing layer and evidence supporting or contradicting each hypothesis;
- history surface used, its time window, permissions, and known latency;
- exact approved correction and any state change receipt;
- verification query/client receipt and observed result; and
- final status: `RESOLVED`, `MITIGATED`, `NOT VERIFIED`, or `ESCALATED`.

## Examples

### Object-resolution diagnosis

```markdown
- Error: 002003 / object does not exist or not authorized
- Query ID: sanitized identifier retained
- Context: correct database; wrong active role
- Object check: object exists under expected fully qualified name
- Grant check: expected role lacks required privilege
- Action: object owner approved and applied least-privilege grant
- Verification: same read-only statement succeeded under workload role
- Status: RESOLVED
```

### Correct inconclusive result

If a just-failed query is absent from Account Usage history, record the surface's
latency and query the bounded Information Schema function. Do not report that the
query did not execute merely because the delayed view has not populated.

## Error Handling

| Condition | Required response |
|---|---|
| Evidence contains credentials or sensitive SQL | Stop distribution, contain the artifact, and produce a redacted receipt |
| Diagnostic role cannot see required history/object | Request narrowly scoped access or an authorized operator's evidence |
| Error number and message disagree | Trust the exact message/context and current documentation, not a memorized number |
| Proposed fix changes grants, keys, compute, or parameters | Require owner approval, change receipt, and reversal plan |
| Connectivity test requires guessed endpoint | Stop and use Snowflake's supported connection test/allowlist workflow |
| Retry succeeds without explaining the failure | Mark `MITIGATED`, retain correlation evidence, and continue root-cause work |
| Verification contradicts diagnosis | Revert where safe and reopen classification |

## Resources

- [Snowflake client connectivity troubleshooting](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/overview)
- [Snowflake troubleshooting tools](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/snowflake-tools)
- [Key-pair authentication troubleshooting](https://docs.snowflake.com/en/user-guide/key-pair-auth-troubleshooting)
- [Information Schema query-history functions](https://docs.snowflake.com/en/sql-reference/functions/query_history)
- [Account Usage QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [Node.js result consumption](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-consume)
- [Python Connector result fetching](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-example)
- [Date and time examples](https://docs.snowflake.com/en/sql-reference/date-time-examples)
