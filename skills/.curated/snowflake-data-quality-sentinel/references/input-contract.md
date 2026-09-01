# Input contract

The analyzer accepts one JSON object with the required top-level fields
`metadata`, `requirements`, `associations`, `measurements`, and
`source_metadata`, plus optional `current_state` and `current_state_receipt`.
Collection and normalization must exclude query/SQL text, filters, raw group
values, endpoints, customer rows, failed-row payloads, PII, credentials, and
signed URLs.

## Metadata

Required fields are `schema_version`, `surface` (`data-quality`), timezone-aware
`collected_at`, `window_start`, `window_end`, and the shared collector's
`collector_receipt_sha256`.

## Requirements

Each required check contains:

- `id`
- `object`: `database`, `schema`, `name`, and `type` (`TABLE` or `VIEW`)
- `metric`: `database`, `schema`, and `name`
- `objective`: null, or `{ "mode": "expectation|anomaly", "name": "..." }`
- `max_result_age_seconds`, `expected_schedule`
- `notification_required`, `expected_execution_role`
- `required_groups`: an array of governed group identifiers

Requirements are owner-approved policy. Discovered measurements cannot add a
required check implicitly.

## Associations

Each association contains `requirement_id`, `reference_id`, `schedule`,
`schedule_status`, `schedule_update_pending`, `notification_status`,
`anomaly_status`, `execution_role`, and `observed_groups`. Requirement and
reference identifiers must be unique.

## Measurements

Each measurement contains `requirement_id`, `reference_id`, timezone-aware
`measured_at`, `evaluation_status`, `expectation_name`, nullable Boolean
`expectation_violated`, nullable Boolean `anomaly_detected`, scalar
`observed_value`, and `observed_groups`.

`measured_at` must fall inside the declared `window_start`/`window_end`.
Future or out-of-window results are invalid evidence, not current health.

Use only the newest measurement for a requirement's current result. Historical
violations remain incident evidence but do not override a newer valid result.

## Source metadata

Each source contains `source`, `kind`, `status`, `collected_at`, nullable
`latest_record_at`, `max_latency_seconds`, `row_count`, and `error_code`.
Recommended kinds are `measurement`, `association`, `usage`, and `notification`.

Map the shared collector's `expectation_status` dataset to measurements and its
`data_quality_usage` dataset to usage-source metadata. Requirements remain a
separate governed input. If association or notification evidence is unavailable,
represent that explicitly in `source_metadata`; never synthesize success. A
source `collected_at` must not precede `window_start` and must be no later than
the envelope `collected_at`; a non-null `latest_record_at` must fall within the
observation window.

## Current-state receipt

When `current_state` is used for monitoring claims, supply the unmodified output
of `collect_snowflake_evidence.py --surface data-quality-current` at root
`current_state_receipt`. The analyzer fail-closes unless the receipt has the
exact v1 collector schema; surface `data-quality-current`; status `collected`;
an empty `errors` array; the exact source view, template name, and bundled SQL
hashes; no selector; a valid canonical `receipt_sha256`; a collection timestamp
equal to `current_state.observed_at`; the reviewed 5000-row cap; internally
consistent row counts; no truncation; and exactly the `data_quality_current`
dataset.

Every current association must match a receipt row by `reference_id`. The row's
metric and referenced object identity must match the governed requirement, and
its schedule status, notification status, and execution role must match the
normalized current association. Notification status is also reconciled. The SQL
does not project the normalized association `status` or notification delivery
timestamp, so those fields remain separate evidence and are not represented as
receipt-bound facts.

## Finding semantics

The analyzer emits all required `DQ_*` codes with independent `quality_impact`
and `monitoring_impact`. A `PASS` is possible only when the requirement denominator
is non-empty and no stronger impact exists. `NO_REQUIRED_CHECKS` is a denominator
statement, not a health claim.
