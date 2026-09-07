# Evidence contract

The analyzer accepts exactly one schema-2 JSON object. Unknown or missing fields
fail closed. All timestamps are canonical UTC (`YYYY-MM-DDTHH:MM:SS[.ffffff]Z`).
Policy identity fields are lowercase 64-character SHA-256 hex values; trusted
digest arguments and receipt hashes use the `sha256:<64 hex>` form.

## Wrapper

```json
{
  "schema_version": "2",
  "policy": {},
  "collector_receipts": [],
  "operator_receipts": [],
  "validation_receipts": []
}
```

The three trust arguments bind different material:

- `trusted-input-sha256` = canonical JSON digest of `{"schema_version": ..., "collector_receipts": ...}`.
- `trusted-policy-sha256` = canonical JSON digest of `policy`.
- `trusted-operator-sha256` = canonical JSON digest of
  `{"operator_receipts": ..., "validation_receipts": ...}`.

Canonical JSON uses UTF-8, sorted keys, no insignificant whitespace, and no ASCII
escaping. Record each digest at the system boundary that approved or collected
that material. Recomputing all three from the same delivered file proves only
self-consistency and must not be called independent trust.

## Policy

```json
{
  "schema_version": "1",
  "analysis_as_of_utc": "2026-09-01T15:00:00Z",
  "mode": "PREFLIGHT",
  "validation_max_age_seconds": 900,
  "expected_group_count": 1,
  "groups": [{
    "lineage_group_key_sha256": "<hex64>",
    "source_account_key_sha256": "<hex64>",
    "source_group_key_sha256": "<hex64>",
    "target_account_key_sha256": "<hex64>",
    "target_group_key_sha256": "<hex64>",
    "expected_object_types_sha256": "<hex64>",
    "expected_allowed_accounts_sha256": "<hex64>",
    "expected_allowed_integration_types_sha256": "<hex64>",
    "expected_replication_schedule_sha256": "<hex64>",
    "rpo_seconds": 3600,
    "rto_seconds": 1800
  }],
  "expected_dependency_count": 0,
  "dependencies": [],
  "expected_validation_count": 1,
  "validations": [{
    "validation_key_sha256": "<hex64>",
    "lineage_group_key_sha256": "<hex64>",
    "stage": "PRE_FAILOVER"
  }]
}
```

Allowed modes are `PREFLIGHT`, `FAILOVER_ATTESTATION`, and
`FULL_DRILL_ATTESTATION`. Counts must equal the exact array lengths; groups,
scopes, and keys must be unique. RPO/RTO must be 1–604800 seconds. Every declared
validation must be no older than the policy-owned 1–604800-second maximum. Every declared
dependency has `dependency_key_sha256`, `lineage_group_key_sha256`, and an
`ordering_proof_sha256`; a null ordering proof blocks readiness.

| Mode | Required validation stages per group |
| --- | --- |
| `PREFLIGHT` | `PRE_FAILOVER` |
| `FAILOVER_ATTESTATION` | `PRE_FAILOVER`, `POST_FAILOVER` |
| `FULL_DRILL_ATTESTATION` | `PRE_FAILOVER`, `POST_FAILOVER`, `POST_FAILBACK` |

## Collector receipt coverage

All collector receipts must be exact live schema-2 outputs from the bundled
reviewed templates, collected within 15 minutes of `analysis_as_of_utc`. The
analyzer verifies source/template/rendered/result/self hashes, source views,
selector bindings, execution context, exact row schemas and counts, a 5,000-row
per-dataset cap, and non-truncation.

| Surface | Required coverage |
| --- | --- |
| `replication-current` | Every source and target account; exactly 1 snapshot/account for preflight, 2 for failover, 3 for full drill |
| `replication` | Exactly 1 receipt per target account; full drill also requires exactly 1 per original source account |
| `replication-progress` | Same directional account coverage as history and the exact same window per account |
| `replication-dangling` | Exactly 1 receipt for each source-local and target-local group scope |

`SHOW FAILOVER GROUPS` is role-filtered. Receipt completeness proves only the
declared scopes under the observed authorization contexts, never account-wide
absence. History/progress functions expose up to 14 days; the collector applies
the stricter 7-day bound and explicit half-open predicates. Each window must end
at or before and within 60 seconds of collection start, at or before observation,
and within 15 minutes of evaluation. A cap hit
invalidates the receipt. Every admitted receipt must identify one organization;
all receipts for one account must additionally share the same collector user,
primary role/type, and secondary-role context.

The current source and target rows must bind to the same declared lineage. The
source primary carries the expected object, allowed-account, integration-type,
and schedule hashes. A secondary at each transition decision point and the final
secondary must report the expected schedule, `STARTED`, and a non-null future next
refresh no later than the RPO horizon. After transitions, the required primary/secondary states
must be independently re-observed.

## Operator receipts

```json
{
  "schema_version": "1",
  "event_key_sha256": "<hex64>",
  "lineage_group_key_sha256": "<hex64>",
  "event": "FAILOVER",
  "source_account_key_sha256": "<hex64>",
  "target_account_key_sha256": "<hex64>",
  "change_record_sha256": "<hex64>",
  "operator_key_sha256": "<hex64>",
  "started_at": "2026-09-01T15:01:00Z",
  "completed_at": "2026-09-01T15:10:00Z",
  "outcome": "SUCCEEDED",
  "receipt_sha256": "sha256:<canonical body digest>"
}
```

Preflight allows no operator receipts. Failover requires exactly one successful,
correctly scoped `FAILOVER` per group. Full drill requires a successful failover
followed by a successful reverse-scoped `FAILBACK`; intervals cannot overlap.
`FAILED`, `PARTIAL`, and `CANCELED` never attest success. Event duration must be
within the group RTO, and current snapshots must prove each primary transition.

## Validation receipts

```json
{
  "schema_version": "1",
  "validation_key_sha256": "<hex64>",
  "lineage_group_key_sha256": "<hex64>",
  "stage": "POST_FAILOVER",
  "observed_at": "2026-09-01T15:11:00Z",
  "status": "PASS",
  "receipt_sha256": "sha256:<canonical body digest>"
}
```

There must be exactly one receipt for every declared validation/stage and no
extras. All must pass and be time-ordered: pre-failover before the event,
post-failover after failover and before failback, and post-failback after failback.
Every validation must also satisfy `validation_max_age_seconds` at evaluation.
The receipt attests only to its owner-defined validation; a login alone does not
prove data or application correctness.

## Verdict rules

Receipt, policy, trust, or attestation-contract errors produce `INCONCLUSIVE`
with `evidence_integrity_status: INVALID`. With valid evidence, any critical
readiness finding produces `NOT_READY`; warning-only findings produce `AT_RISK`.
Only a clean, completely covered bundle reaches the positive status for its mode.
Positive statuses end in `_AS_OF` and the report binds them to
`analysis_as_of_utc`, the admitted evidence observation range, and
`valid_until_utc`. They are historical statements, never timeless readiness
claims; `valid_until_utc` equals the as-of instant because the deterministic
analyzer has no independently trusted live clock or refresh service. Consumers
must reject them after that instant and collect fresh evidence for a new verdict.

RPO is derived only from the unique `PRIMARY_SNAPSHOT_TIMESTAMP` attached to the
latest job before the relevant decision point whose terminal phase is uniquely
`COMPLETED`. Preflight anchors at evaluation, failover at failover start, and full
drill additionally evaluates the original source's reverse refresh at failback
start. The job is unproved if
its terminal phase is failed, canceled, missing, duplicated, or its snapshot is
missing/ambiguous. Progress independently shows its latest phase as `COMPLETED`;
history operation starts and progress phase starts are not treated as a shared
correlation key. A non-null progress end cannot fall after the decision point.
Snowflake leaves terminal progress percentages empty, so percentage is not a
completion signal. A blocking dangling reference is critical; a nonblocking one is a
warning. Reports contain finite finding codes and hashed scopes, not input rows.
