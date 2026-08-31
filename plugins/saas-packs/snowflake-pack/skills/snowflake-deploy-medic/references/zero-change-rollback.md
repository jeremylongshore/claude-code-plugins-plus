# Zero-change and rollback gate

The deploy medic is complete only when an operator can show what would change,
what would not change, and how to stop safely. A saved plan, migration dry-run,
toolchain receipt, and rollback test belong together.

## Zero-change adoption

After importing existing Terraform resources into their intended addresses,
refresh and run a fresh plan against the correct account/role/workspace. Treat
`terraform plan -detailed-exitcode` as:

- `0`: no changes in the reviewed scope;
- `2`: valid preview with changes requiring review;
- any other non-zero value: plan error, not a safe preview.

For grant-heavy adoption, inspect the plan for privilege removals, ownership
changes, future-grant scope, provider normalization, and resources that would be
replaced. A zero-change plan at the wrong account or with incomplete state is a
false receipt, so include account identity and state lineage without secrets.

## Rollback is change-specific

There is no universal “rollback” for a Snowflake deployment:

- Terraform may restore configuration/state, but an already-applied privilege,
  ownership transfer, data DDL, or external integration can have side effects.
- A versioned migration is normally forward-only; create a compensating migration
  rather than editing history.
- A repeatable migration can rerun by checksum, so test idempotence and its
  effect on views/procedures before releasing it.
- Data changes require a bounded backup/time-travel/replay plan with explicit
  retention and duplicate boundaries.

The receipt must name the exact plan/migration set, preconditions, operator,
rollback or forward-fix commands for a separately approved run, validation
queries, and the stop condition. “We have a snapshot” is not a rollback test.

## No automatic apply

This skill may inspect configuration, a saved plan, dry-run output, and release
notes. It never calls `terraform apply`, `terraform destroy`, `schemachange deploy`,
`snow sql` with mutation, or Snowflake DDL/DML on the user's behalf. If the user
asks to execute, show the reviewed command and require an explicit approval at the
mutation boundary.

Primary references: [Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan),
[Terraform detailed exit codes](https://developer.hashicorp.com/terraform/cli/commands/plan#detailed-exit-codes),
and [Snowflake Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel).
