# Snowflake Error Diagnostic Reference

Run only the queries relevant to the observed failure with an authorized,
least-privileged role. Substitute identifiers through the approved client rather
than concatenating untrusted input. Keep query text, bind values, credentials,
account identifiers, and personal data out of shared output.

## Contents

1. [Session context](#session-context)
2. [Recent query failures](#recent-query-failures)
3. [Object and warehouse evidence](#object-and-warehouse-evidence)
4. [Key-pair JWT evidence](#key-pair-jwt-evidence)
5. [Connectivity evidence](#connectivity-evidence)
6. [Large-result handling](#large-result-handling)
7. [Timeout and performance evidence](#timeout-and-performance-evidence)

## Session Context

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_USER(), CURRENT_ROLE(),
       CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE(), CURRENT_SESSION();
```

Record only the fields allowed by the incident's evidence policy. `NULL` context
does not itself identify an error; compare it to what the failed statement needs.

## Recent Query Failures

Use Information Schema for current triage. Bound the time and result count before
the outer filter because Snowflake applies table-function arguments first:

```sql
SELECT query_id, execution_status, error_code, error_message,
       start_time, end_time, total_elapsed_time,
       role_name, database_name, schema_name, warehouse_name
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  END_TIME_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP()),
  RESULT_LIMIT => 1000
))
WHERE error_code IS NOT NULL
ORDER BY start_time DESC;
```

This function covers activity within the last seven days and visibility depends on
the executing role's privileges. Avoid selecting `query_text` and `bind_values` by
default.

For older or account-wide analysis, use `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`
with an explicit time predicate. Its data can lag by up to 45 minutes:

```sql
SELECT query_id, execution_status, error_code, error_message,
       start_time, end_time, total_elapsed_time,
       role_name, database_name, schema_name, warehouse_name
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
  AND error_code IS NOT NULL
ORDER BY start_time DESC;
```

Do not compare the two surfaces without accounting for visibility, retention, and
latency differences.

## Object and Warehouse Evidence

For an object-resolution failure:

```sql
SHOW TABLES LIKE 'TARGET_TABLE' IN SCHEMA TARGET_DB.TARGET_SCHEMA;
SHOW GRANTS ON TABLE TARGET_DB.TARGET_SCHEMA.TARGET_TABLE;
SHOW GRANTS TO ROLE TARGET_ROLE;
```

Run the command matching the actual object type; a table command does not prove a
view, stage, function, or dynamic table exists. Quoted identifiers are case-
sensitive. Never issue a `GRANT` from a troubleshooting template.

For a warehouse-context failure:

```sql
SELECT CURRENT_WAREHOUSE();
SHOW WAREHOUSES LIKE 'TARGET_WH';
SHOW GRANTS ON WAREHOUSE TARGET_WH;
```

Inspect state, type, auto-resume configuration, and privileges from the actual
output. Select or resume compute only under the workload's approved change policy.

## Key-pair JWT Evidence

Preserve the UUID shown after `JWT token is invalid`. Snowflake documents
`SYSTEM$GET_LOGIN_FAILURE_DETAILS` for an authorized administrator:

```sql
SELECT SYSTEM$GET_LOGIN_FAILURE_DETAILS('REPLACE_WITH_FAILURE_UUID');
DESCRIBE USER TARGET_LOGIN;
```

Compare the detailed error with:

- the client account identifier and the JWT issuer account identifier;
- the configured username and the user's `LOGIN_NAME`;
- the JWT algorithm and the expected Snowflake requirement;
- host clock synchronization;
- the token's public-key fingerprint and `RSA_PUBLIC_KEY_FP` or
  `RSA_PUBLIC_KEY_2_FP` from `DESCRIBE USER`; and
- the approved key-rotation state.

The private key must never be copied into the diagnostic record. A mismatch calls
for a controlled key/claim/configuration correction, not unconditional key creation.

## Connectivity Evidence

Prefer the supported Snowflake CLI test with a named, preconfigured connection:

```bash
snow connection test --connection incident-readonly
```

Snowflake also documents a diagnostic mode in the Python Connector. Use Snowflake's
allowlist workflow to identify required service and stage endpoints. If an operator
must use `curl` for a specific URL, validate that exact destination against the
allowlist and capture only status/timing—not headers, signed query strings, bodies,
or credentials.

Do not print account/user/password environment variables, construct a hostname from
unsanitized input, or call an undocumented authentication endpoint as a health check.
Network failures can involve DNS, proxy, TLS inspection, OCSP, or stage endpoints;
one account-host probe does not cover all of them.

## Large-result Handling

Snowflake recommends Node.js streaming when a result might exceed Node's memory:

```typescript
connection.execute({
  sqlText: approvedSql,
  streamResult: true,
  complete: (error, statement) => {
    if (error) throw error;
    statement
      .streamRows()
      .on('data', processRow)
      .on('error', handleError)
      .on('end', finish);
  },
});
```

The Python Connector documents `fetchone()` or `fetchmany()` when the result set is
too large for memory:

```python
cursor.execute(approved_sql)
while rows := cursor.fetchmany(batch_size):
    process_batch(rows)
```

Choose and bound `batch_size` from application memory and processing evidence. Use
binds or approved static SQL; never interpolate untrusted values into `approvedSql`.

## Timeout and Performance Evidence

Inspect the configured parameter hierarchy rather than assuming a value:

```sql
SHOW PARAMETERS LIKE 'STATEMENT_TIMEOUT_IN_SECONDS' IN SESSION;
SHOW PARAMETERS LIKE 'STATEMENT_QUEUED_TIMEOUT_IN_SECONDS' IN SESSION;
```

Use the query profile and bounded history columns to distinguish:

- compilation versus execution time;
- warehouse provisioning, overload, repair, and transaction-block queueing;
- bytes and partitions scanned;
- local and remote spill;
- actionable query retry cause versus fault-handling time; and
- client result-fetch failures after successful server execution.

Changing a timeout can increase resource consumption without correcting the query.
Resizing or changing warehouse configuration can change cost and concurrency. Make
either change only with evidence, approval, a verification plan, and a reversal.

## Official References

- [QUERY_HISTORY functions](https://docs.snowflake.com/en/sql-reference/functions/query_history)
- [Account Usage QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [Key-pair troubleshooting](https://docs.snowflake.com/en/user-guide/key-pair-auth-troubleshooting)
- [Connectivity tools](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/snowflake-tools)
- [Node.js streaming results](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver-consume)
- [Python Connector fetching](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-example)
