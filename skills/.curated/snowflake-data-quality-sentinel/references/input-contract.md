# Input contract

The analyzer accepts one JSON object with exactly five top-level fields:
`metadata`, `requirements`, `associations`, `measurements`, and
`source_metadata`. Collection and normalization must exclude query/SQL text,
customer rows, failed-row payloads, PII, credentials, and signed URLs.

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

## Finding semantics

The analyzer emits all required `DQ_*` codes with independent `quality_impact`
and `monitoring_impact`. A `PASS` is possible only when the requirement denominator
is non-empty and no stronger impact exists. `NO_REQUIRED_CHECKS` is a denominator
statement, not a health claim.
