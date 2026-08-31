# schemachange integrity and migration review

schemachange is a Python database change-management tool maintained in the
[Snowflake-Labs/schemachange repository](https://github.com/Snowflake-Labs/schemachange).
It is community-developed, so verify the installed release and current
documentation rather than treating it as a Snowflake service guarantee.

## Versioned, repeatable, and always scripts

- **Versioned (`V...__...sql`)** scripts are applied once by version and tracked
  in `CHANGE_HISTORY`. Once applied, do not edit their contents in place: a
  checksum change is evidence of drift and can make an environment diverge.
- **Repeatable (`R__...sql`)** scripts are reapplied when their checksum changes.
  Their SQL must be idempotent and the rerun must be intentional; checksum change
  is not an incident by itself.
- **Always (`A__...sql`)** scripts run each deployment by design. They need an
  explicit cost/side-effect review and should not be confused with repeatables.

Collect `VERSION`, `SCRIPT`, `SCRIPT_TYPE`, `CHECKSUM`, `STATUS`, and
`INSTALLED_ON` from the change-history table and compare it with the exact
repository commit. The analyzer reports versioned checksum drift, repeatable
checksum changes, and duplicate version names; it never edits history or runs a
migration.

## Safe preview and ordering

Use the installed tool's current `verify`/`dry-run` behavior and pin the command
in CI. A parallel branch can create a lower version after a higher version has
already run; determine whether the environment intentionally permits out-of-order
execution and review dependency ordering. Do not enable out-of-order merely to
silence a skipped migration.

For a checksum drift, stop and choose one of these documented paths: restore the
original applied script, create a new versioned migration, or explicitly approve a
repeatable conversion with a tested rollback/forward-fix. Do not “fix” the change
history table by hand.

## Upgrade-specific checksum risk

Schemachange release notes have documented checksum regressions and fixes around
rendering/trailing semicolons. Before upgrading, read the live
[release notes](https://github.com/Snowflake-Labs/schemachange/releases) and
[troubleshooting guide](https://github.com/Snowflake-Labs/schemachange/blob/master/TROUBLESHOOTING.md),
then run the tool's verification/dry-run against a copy of the target history.
Record the exact installed version and expected checksum diff.

## Credentials

Use the tool's supported key-pair, OAuth, workload identity, or external-browser
authentication mechanism. Never put a private-key passphrase, token, or password
in command-line arguments, migration files, receipts, or CI logs.
