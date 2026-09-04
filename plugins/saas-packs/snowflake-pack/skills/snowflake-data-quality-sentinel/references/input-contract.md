# Schema-2 input contract

The analyzer accepts exactly:

```json
{
  "schema_version": "2",
  "policy": {
    "schema_version": "1",
    "expected_requirement_count": 1,
    "analysis_as_of_utc": "2026-09-03T12:00:00Z",
    "history_assumption_delay_seconds": 1800,
    "history_assumption_status": "OWNER_DECLARED_NOT_PROVIDER_GUARANTEED",
    "requirements": []
  },
  "collector_receipts": []
}
```

`analysis_as_of_utc` must equal the explicit analyzer evaluation time.
`history_assumption_delay_seconds` is an owner-declared integer from 0 through
604800, or null. It is recorded as an assumption and never proves provider
settlement or completeness. The trusted evidence digest covers only
`schema_version` plus `collector_receipts`; a separately owner-approved policy
file has its own trusted digest and must exactly match the wrapper policy.

## Policy requirement

Every requirement has exactly these fields:

- Lowercase 64-hex identity fields: `requirement_key_sha256`,
  `object_key_sha256`, `association_key_sha256`, `metric_key_sha256`,
  `expectation_key_sha256`, `definition_sha256`, and `schedule_sha256`.
- Nullable lowercase 64-hex `expected_execution_role_sha256`, `filter_sha256`,
  and `group_definition_sha256`.
- Nullable integer `expected_group_limit` from 1 through 1000.
- `object_domain`: `TABLE` or `VIEW`.
- `schedule_mode`: `INTERVAL`, `CRON`, or `TRIGGER_ON_CHANGES`.
- Positive integer `max_result_age_seconds`, Boolean `notification_required`, and
  `objective_mode`: `EXPECTATION` or `ANOMALY`.

The expected count must exactly equal the array length. Requirement keys and the
pair `(association_key_sha256, expectation_key_sha256)` are unique. Multiple
expectations may share one association when their association-level policy is
consistent. Requirements are owner-approved policy; discovered Snowflake rows
cannot enlarge or shrink this denominator.

Identity hashes are scoped by organization and account. Object identity includes
database, schema, and object name. Metric identity includes metric database,
schema, and name. The association's Snowflake `REF_ID` hash binds the exact applied
overload because the history surface does not expose a compatible signature
format. Tests and reports treat all hashes as opaque and never recover their
source strings.

## Required receipts

Every receipt must use collector schema 2, `live-cli`, the exact reviewed template
and source list, one execution-context row, exact dataset counts and result hash,
per-dataset cap metadata, the fixed collector non-claims, a maximum 130-second
collection interval, and a self-checksum. Both collection completion and
`observed_at` must be no more than 900 seconds old at evaluation. The analyzer
additionally requires the independently trusted evidence digest.

For selector-bound surfaces, `source_row_count` is the uncapped `COUNT(*)` and can
exceed the number of emitted rows. It must equal emitted rows below the 5000-row
cap and must never be smaller. A count at or above the cap requires both context
and receipt truncation flags and suppresses classification.

Exactly one `data-quality` receipt is required with datasets
`execution_context` and `expectation_history`. For every distinct governed object,
exactly one receipt is required for each live Information Schema surface:

| Surface | Exact datasets |
|---|---|
| `data-quality-associations-current` | `current_associations`, `execution_context` |
| `data-quality-expectations-current` | `current_expectations`, `execution_context` |

For each distinct notification-required governed object, one selector-bound
`data-quality-notification-current` receipt is required with exact datasets
`execution_context` and `notification_associations`. Each selector-bound receipt
uses exact Boolean selector declarations, an exact hashed object/domain binding,
and the reviewed privacy-bound rendered-SQL digest. Duplicate, missing, or
ungoverned bindings are rejected.

All receipts must share organization, account, collector user, primary role and
role type, secondary-role set, and UTC timezone. Selector-bound current receipts
come from live Information Schema functions and carry no Account Usage lag or
watermark claim.

## Result semantics

History uses a half-open UTC window of at most seven days. Results match all of
object, association, metric, expectation, and definition hashes. Only the newest
exact match is classified.

`expectation_violated` has three distinct meanings: false is
`SATISFIED_OBSERVATION`, true is `VIOLATION_OBSERVED`, and null is
`EVALUATION_FAILED_OBSERVED`. An absent fresh exact match is `NOT_OBSERVED`.
Out-of-policy history rows contribute only to `out_of_scope_observation_count`;
their hashes never become finding scopes or output values.

Configuration status is `PASS`, `FAIL`, or `INCONCLUSIVE`. Quality status is
`FAIL` only for an exact trusted fresh violation and otherwise `INCONCLUSIVE`.
History completeness is always `UNPROVEN_NO_PROVIDER_SLA`, `pass_supported` is
always false, and `settled_through_utc` is null. No owner delay turns an absence or
satisfied observation into present-tense proof of quality.

No receipt or report contains raw object, metric, expectation, signature,
schedule, role, filter, group, SQL, connection-profile, query-ID, or customer-row
values.
