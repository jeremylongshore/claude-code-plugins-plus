# Evidence contract

The analyzer accepts one exact schema-2 object. Unknown fields fail closed.

`release` binds `package_key_sha256`, `distribution` (`INTERNAL|EXTERNAL`),
`release_channel` (`QA|ALPHA|DEFAULT`), exact target version/patch, manifest
version, prior manifest version, `MAJOR|PATCH` release kind, an
`automated_privileges_changed` boolean, exact expected cohort/group and installed
instance counts, and independently trusted manifest/setup digests. It also contains:

- `expected_setup_statement_count` and ordered `setup_statements`; each row has
  `statement_key_sha256`, one-based `ordinal`, `replay_safe`, `grant_effect`
  (`NONE|PRESERVES_GRANTS|REMOVES_GRANTS`), nullable `restore_ordinal`, and
  `forbidden_construct`.
- `expected_privilege_delta_count` and `privilege_deltas`; each uses hashed
  principal/object/delta keys and finite `ADD|REMOVE` action.
- `expected_reference_count` and `references`; each binds a reference hash,
  object-type hash, privilege-set digest, and `callback_registered`.
- `expected_app_spec_delta_count` and `app_spec_deltas`; each binds a spec hash,
  definition digest, `ADD|CHANGE|REMOVE`, positive sequence, and consumer status
  `APPROVED|PENDING|DECLINED|NOT_OBSERVED`.

`receipts` contains exactly `native-app-versions-current`,
`native-app-release-directives-current`, and
`native-app-upgrade-cohorts-current`. Each must be a live schema-2 collector
receipt, no older than 15 minutes, with exact canonical SQL/source/dataset hashes,
one same-statement context, `row_limit: 5000`, `cap_scope: per_dataset`, and no
cap hit. Every row and context selected-package hash must equal `release` scope.
All three authorization account hashes must match. The separate cohort digest
covers the cohort rows together with `expected_cohort_count` and
`expected_installed_instance_count`; their `instance_count` sum must equal that
trusted installed-instance denominator.

`compatibility` has exact `expected_count` and `rows`. One `COMPATIBLE` row for
every distinct observed current version/patch must target the proposed exact
version/patch. Extra compatibility claims do not fill a missing observed edge.

`lifecycle` has `expected_event_count`, exact finite install/upgrade/uninstall
events, independently supplied self-consistent receipt digest, and observation
time. Each event binds its scoped package and cohort hashes, exact version/patch,
finite outcome, and a fresh, non-future timestamp. Every current cohort must have
a bound event, and every event version must exist in the current version receipt.
It complements the non-retained current snapshot;
it never makes a missing consumer row proof of health.

`rollback` binds the previous exact version/patch, artifact digest, tested flag,
privilege-preservation result, App Spec reconciliation result, and independent
owner receipt digest. That trusted digest covers the full rollback receipt after
excluding only its own digest field, so an arbitrary or changed artifact hash
cannot pass. It proves only that the supplied rollback plan was tested,
not that Snowflake will perform it or that the analyzer authorizes it.

Trusted hashes use lowercase `sha256:<64 hex>`. Snowflake-scoped identity keys use
lowercase 64 hex without a prefix. Timestamps are canonical UTC `...Z`. Counts
are native nonnegative integers; booleans are native booleans. No raw names,
consumer identities, SQL, errors, definitions, credentials, or payload values
are accepted.

`provider_latency_documented` is a native boolean and `primary_role_type` is
limited to Snowflake's supported `ROLE|APPLICATION_INSTANCE` results. Provider
timestamps must be canonical, parseable UTC and not later than the same-statement
observation; App Spec approvals and lifecycle observations must also be fresh and
non-future. Directive natural identity is its complete target, target-version,
status, channel, maintenance-window, deadline, and modification projection;
cohort natural identity is its complete current/previous/upgrade/target tuple.
Duplicate natural identities fail even when opaque row hashes differ. A v2 PATCH
with any automated ADD or REMOVE delta blocks regardless of a contradictory
`automated_privileges_changed: false`; App Spec CHANGE requires exactly the next
sequence number.

`READY_FOR_OPERATOR_RELEASE_AS_OF` requires every integrity, freshness,
denominator, scan, setup replay, privilege/reference/App Spec, compatibility,
cohort, lifecycle, and rollback condition. It is still an observation—not a
publish/upgrade instruction, consumer approval, future guarantee, or permission.
