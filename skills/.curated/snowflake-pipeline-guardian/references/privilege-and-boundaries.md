# Pipeline guardian privilege and safety boundary

The guardian is a read-only evidence collector and classifier. It never executes
or emits runnable commands to resume, suspend, execute, refresh, recreate,
replace, copy, replay, insert, merge, truncate, or drop anything. A recovery plan
may describe an approval-gated change category and its prerequisites, but the
change itself remains outside this skill.

## Least-privilege collection

Use an approved role scoped to the incident. The security owner, not this skill,
decides any additional grant. Depending on account policy, collection can require:

- visibility of the relevant task, stream, dynamic table, and pipe objects;
- the applicable monitor privilege for task, dynamic-table, and pipe metadata;
- access to the three reviewed `SNOWFLAKE.ACCOUNT_USAGE` history views; and
- parent database/schema usage needed to inspect the named objects.

Do not default to `ACCOUNTADMIN`. A failed query, missing row, or null metadata
field is an observability gap, not evidence that an object is absent or broken.
`SHOW ... IN ACCOUNT` remains limited to objects visible to the active
authorization context. The receipt binds hashed organization/account/user/role
context so evidence collected under different contexts cannot be silently
combined, but it does not prove that the role can see the whole account.

For a selected pipe, Snowflake restricts `SYSTEM$PIPE_STATUS` to appropriately
privileged roles. Failure to collect one projected status receipt leaves that
pipe unresolved; do not substitute a receipt from another role, account, or
selector.

Primary access references:

- [Snowflake access-control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Task access control](https://docs.snowflake.com/en/user-guide/tasks-intro#label-tasks-access-control)
- [Dynamic-table access control](https://docs.snowflake.com/en/user-guide/dynamic-tables-privileges)
- [SHOW PIPES usage notes](https://docs.snowflake.com/en/sql-reference/sql/show-pipes#usage-notes)
- [SYSTEM$PIPE_STATUS usage notes](https://docs.snowflake.com/en/sql-reference/functions/system_pipe_status#usage-notes)

## Privacy boundary

The reviewed SQL hashes identity fields with organization/account scope and
projects only required states, enums, booleans, counts, and timestamps. Preserve
that projection. Do not add or share:

- raw object, database, schema, warehouse, role, user, query, stage, pipe, or file
  identifiers;
- SQL/DDL text, predicates, task definitions, comments, schedules,
  target-completion intervals, target-lag text, or provider reason codes;
- raw `SYSTEM$PIPE_STATUS`, paths, channel names, integrations, errors, faults,
  or free-text state/error messages;
- credentials, tokens, private keys, connection strings, presigned URLs,
  customer records, payloads, or PII; or
- raw Snowflake CLI profile names.

The pipe selector is used only inside the trusted operator environment. A
successful receipt carries presence/fingerprint plus a scoped object hash, never
the raw selector. Its rendered-SQL digest covers a receipt-only privacy-bound
rendering that substitutes the scoped hash for that selector. Before a scoped
hash exists, an error receipt uses the reviewed template digest and a null
selector fingerprint. Account-scoped hashes remain linkable pseudonyms and must
be protected as operational data.

## Evidence boundary

Classify every statement as one of:

- **Observed:** present in a validated projected receipt.
- **Derived:** deterministically computed from trusted, complete evidence.
- **Unknown:** hidden, stale, capped, unsettled, missing, or inconsistent.
- **Hypothesis:** plausible but still requiring read-only evidence or owner
  confirmation.

Receipt self-digests detect accidental or post-collection changes but are not
trust anchors. The separately recorded canonical bundle digest is an operator
assertion of byte identity only; it is not a signature or proof of Snowflake
origin. Offline-normalized, pasted, or manually mapped data stays advisory.

Current `SHOW` state and historical Account Usage answer different questions.
Never use one to fill the other's coverage gap. A bounded row-absence observation
requires completion/end time before the recorded settlement cutoff, an uncapped
dataset, and the same authorization context; it still is not account-wide
absence. Current receipts expire after 15 minutes relative to the explicit
evaluation timestamp. Context-equivalent receipts collected within 15 minutes
still do not form an atomic transaction snapshot.

`SYSTEM$STREAM_HAS_DATA` is outside the approved evidence surfaces because its
call can affect stream staleness behavior. Raw pipe-status JSON is also outside
the boundary; only the selector-bound privacy projection is admissible.
