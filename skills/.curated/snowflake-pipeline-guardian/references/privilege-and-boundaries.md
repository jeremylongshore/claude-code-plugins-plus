# Pipeline guardian privilege and safety boundary

The guardian is an evidence collector and reasoning aid. It must never run a
mutating Snowflake statement automatically. In particular, it never issues
`ALTER TASK ... RESUME/SUSPEND`, `EXECUTE TASK`, `ALTER DYNAMIC TABLE ... REFRESH`,
`CREATE OR REPLACE STREAM`, `CREATE OR REPLACE TABLE`, `INSERT`, `MERGE`, `COPY`,
`TRUNCATE`, or `DROP`.

## Minimum read-only evidence

Use the narrowest role that can inspect the named objects. Depending on the
account's grant model, an operator may need:

- `MONITOR` on tasks and dynamic tables for state/history visibility.
- `USAGE` on the database and schema plus object-level visibility.
- Access to the relevant `INFORMATION_SCHEMA` table functions.
- `MONITOR` or equivalent visibility for warehouse/query history.
- Read access to the stage and cloud notification configuration metadata for a
  Snowpipe path audit.

Do not tell a user to run as `ACCOUNTADMIN` merely because a query failed. Ask
which row or view is hidden, then request the smallest grant from the account's
security owner. A missing privilege is a finding about observability, not proof
that the pipeline is failing.

## Redaction

Inputs may contain query text, stage URLs, role names, file names, and error
messages. Before sharing a receipt, redact credentials, tokens, private keys,
customer payloads, presigned URLs, and PII. Query IDs and timestamps are usually
the useful correlation keys. Never send raw `SYSTEM$PIPE_STATUS` output if it
contains a secret-bearing integration endpoint.

## Evidence quality

Each diagnosis should distinguish:

- **Observed:** a supplied state, error, timestamp, row, or count.
- **Derived:** a classification computed by the deterministic analyzer.
- **Unknown:** a missing or privilege-hidden field.
- **Hypothesis:** a plausible cause requiring a query or owner confirmation.

The skill operates in advisory mode when Snowflake connectivity, a configured
warehouse, or required privileges are absent. Pasted evidence is acceptable, but
its collection time and source must be recorded. Do not use a current clock to
silently widen a query window or convert unknowns into “healthy.”

Primary access references: [Dynamic table access control](https://docs.snowflake.com/en/user-guide/dynamic-tables-privileges),
[task privileges](https://docs.snowflake.com/en/user-guide/tasks-intro#label-tasks-access-control),
and [Snowflake access control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview).
