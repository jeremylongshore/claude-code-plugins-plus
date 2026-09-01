# Dry-run remediation and rollback packet

The analyzer emits a `dry_run_packet` for review. It is intentionally not an
executable runbook.

## Remediation entries

Each finding produces an ordered entry with its code, release surface, required
evidence, and next read-only verification. Collect a new immutable input receipt
after remediation. Do not edit a report or suppress a finding.

For setup defects, rerun the isolated fresh-install/restart/repeat/upgrade tests
after correcting the candidate artifact. For privilege or App Spec changes,
produce consumer disclosure and approval evidence. For scan and channel state,
an operator performs any authorized change separately; this skill only consumes
the resulting `SHOW` evidence.

## Rollback boundary

The packet identifies a previously tested artifact and stop conditions. It does
not assert that Snowflake can synchronously downgrade every installed app.
Provider release recovery may require halting a cohort, repairing forward, or a
new patch/version depending on consumer and channel state. The named change owner
chooses the action inside an approved window.

Minimum observables are upgrade failures, disabled application instances, and an
application-specific invariant. Threshold, source, and observation window must be
declared before approval. A rollback target without its artifact hash, baseline
hash, owner, tested dry-run, halt plan, or stop conditions is unbounded.

## Prohibited actions

The packet always repeats that the analyzer did not register, publish, add, drop,
deregister, set a directive, upgrade, grant, revoke, or execute setup SQL. A
`READY_FOR_EXPLICIT_APPROVAL` gate is evidence for an operator decision only.
