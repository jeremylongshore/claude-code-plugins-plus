# Native App release evidence contract

The analyzer accepts one JSON object with `schema_version: "1"`. Use exact JSON
types. Timestamps are timezone-aware ISO 8601 values; hashes use
`sha256:<64 lowercase hexadecimal characters>`.

## Required root sections

- `as_of`: decision timestamp, not in the future.
- `package`: `name`, `candidate_version`, non-negative integer
  `candidate_patch`, `change_kind` (`VERSION` or `PATCH`), and candidate
  `artifact_sha256`.
- `source_review`: one entry per required topic: `setup_script`,
  `manifest_privileges`, `app_specifications`, `security_scan`,
  `release_channels`, `upgrades`, and `release_notes`. Each entry contains a
  Snowflake documentation URL and `reviewed_at`.
- `manifest.previous` and `manifest.candidate`: `manifest_version`,
  source hash, `setup_script`, `privileges`, `references`, and `app_specs`.
- `manifest.consumer_disclosure`: exact booleans
  `privilege_delta_reviewed` and `app_spec_delta_reviewed`.
- `setup_script`: path/hash, parse state, four test booleans, test receipt hash,
  normalized `statements`, and the static parser receipt.
- `artifact_receipt`: exact candidate/version/patch, previous and candidate
  manifest source hashes, hashes of both normalized manifest payloads, setup
  source hash, file count, and candidate bundle hash.
- `security_scan`: `review_status` and `observed_at`.
- `compatibility`: immediately prior version, supported upgrade origins,
  manifest/setup-pair test, state-change declaration, contract-test results, and
  an exact self-hashed receipt bound to the candidate artifact.
- `channels`: every relevant QA/ALPHA/DEFAULT channel, current version list,
  whether the candidate is already present, target flag, and observation time.
- `cohorts`: complete per-target-channel consumer counts, source versions,
  preflight result, disabled/failed counts, rollback readiness, and observation.
- `channel_receipt`, `cohort_receipt`, and `retirement_receipt`: exact copies of
  their corresponding payloads plus source, collection time, row count,
  `truncated: false`, artifact hash, and canonical receipt hash.
- `retirements`: every proposed old-version removal and its observed completion
  state. Use an empty array and a valid zero-row receipt when none is proposed.
- `rollback`: exact self-hashed receipt containing owner, target version/artifact,
  baseline, dry-run test state/time, halt plan, stop conditions, and observables.

## Normalized manifest values

Each privilege is `{ "name": ..., "description": ... }`. Each reference is
`{ "name": ..., "object_type": ..., "privileges": [...] }`. Each App Spec is
`{ "name": ..., "type": ..., "sequence": <integer>,
"definition_sha256": ... }`. Names must be unique within a list.

The analyzer derives privilege, reference, and App Spec deltas. A changed App
Spec definition must have a larger sequence than the previous definition. Patch
releases cannot change manifest version or privilege requests. Changing manifest
version from 2 to 1 is a revocation risk and blocks preflight.

## Normalized setup statements

Do not include SQL. Each statement is an object containing:

```json
{
  "index": 1,
  "operation": "CREATE_IF_NOT_EXISTS",
  "object_type": "APPLICATION_ROLE",
  "object_name": "APP_USER",
  "idempotent": true,
  "stateful": false
}
```

Allowed operations are `CREATE_IF_NOT_EXISTS`, `CREATE_OR_ALTER`,
`CREATE_OR_REPLACE`, `ALTER_IDEMPOTENT`, `MERGE_GUARDED`, `GRANT`, and `OTHER`.
Every statement must be explicitly assessed. `CREATE_OR_REPLACE` on an
`APPLICATION_ROLE`, a non-idempotent statement, or `CREATE_OR_REPLACE` on a
stateful object blocks the release. `OTHER` is an unclassified statement and also
blocks; a parser cannot claim `ambiguous: false` while leaving executable setup
semantics unclassified.

The static parser receipt must bind the candidate artifact, setup source hash,
SHA-256 of the complete normalized statement array, parser version, candidate
version/patch, and exact statement count. Both `ambiguous` and `executed` must be
`false`. The parser may classify SQL but must never probe or execute it.

## Receipt integrity

Every receipt uses `schema_version: "1"`, its exact documented `source`, a
candidate `artifact_sha256`, `collected_at`, exact `row_count`,
`truncated: false`, surface-specific payload bindings, and `receipt_sha256`.
`receipt_sha256` is SHA-256 over canonical JSON (keys sorted, no insignificant
whitespace, UTF-8) after removing only `receipt_sha256`.

The analyzer checks exact field sets, canonical receipt hashes, candidate
artifact links, source identifiers, payload equality, counts, truncation, and
freshness. A syntactically valid hash string without those relationships is not
proof. Missing, stale, mismatched, extra-field, tampered, or truncated receipts
block the gate.

## Channels, cohorts, and retirement

`channels[].versions` is the currently observed version set. The analyzer adds
the candidate for projected capacity unless `candidate_already_present` is true.
A target channel with a projected count above two blocks preflight. Duplicate or
unknown channels are invalid input.

Every target channel needs at least one cohort record, including an explicit
zero-consumer cohort. `observed_count` must equal `consumer_count`; all source
versions must be compatible; disabled or failed instances block the cohort.

A retirement item has `channel`, `version`, `state` (`PLANNED`, `IN_PROGRESS`, or
`COMPLETE`), `consumers_remaining`, `running_code_remaining`, and `observed_at`.
Only `COMPLETE` with both counts at zero proves removal. A request or elapsed time
does not prove completion.

## Rollback observables

An observable has `name`, `source`, `threshold`, and positive `window_minutes`.
The rollback packet must cover at least `upgrade_failures`, `disabled_instances`,
and one application-specific invariant. The analyzer validates the denominator
and emits the normalized observables; it does not execute a rollback.

## Freshness and privacy

Source reviews must be no older than 30 days. Scan, channel, cohort, retirement,
and rollback test evidence must be no older than 60 minutes relative to `as_of`.
Future timestamps are invalid. Remove passwords, tokens, credentials, private
keys, authorization headers, raw SQL, query text, customer rows/data, PII, and
presigned URLs. Evidence collection failures remain blockers.
