# Evidence contract

The analyzer accepts one JSON object with `schema_version: "1"`.

## Identity and privacy

Use stable opaque keys such as `asset_012`, `tag_pii`, `policy_mask_4`, and
`scenario_analyst`. Do not export fully qualified object names, raw tag values,
policy bodies, SQL text, data values, user names, role names, or credentials.
Entity keys for aggregation precedence must be `sha256:<64 lowercase hex>`.

Arrays are bounded at 10,000 denominator assets and 50,000 rows per evidence
surface. Partition a larger review and preserve a receipt per partition.

## Required top-level fields

```json
{
  "schema_version": "1",
  "metadata": {
    "assessed_at": "2026-08-31T12:00:00Z",
    "edition": "ENTERPRISE",
    "preview_features_enabled": ["TAG_BASED_PROJECTION_POLICY"],
    "max_age_hours": {"evidence": 4, "classification": 720}
  },
  "assets": [],
  "tags": [],
  "classifications": [],
  "policies": [],
  "policy_context": [],
  "receipts": {}
}
```

Every asset declares `asset_key`, `domain` (`COLUMN`, `TABLE`, or `VIEW`),
`require_tag`, `require_classification`, and `required_controls`. Supported
controls are `MASKING_POLICY`, `ROW_ACCESS_POLICY`, `PROJECTION_POLICY`,
`JOIN_POLICY`, and `AGGREGATION_POLICY`.

Tag rows contain `asset_key`, opaque `tag_key`, and `apply_method`:
`CLASSIFIED`, `MANUAL`, `PROPAGATED`, `INHERITED`, or `LEGACY`. The analyzer
does not accept or need a tag value.

Classification rows contain `asset_key`, `status`, `last_classified_on`,
`last_attempt_on`, and `error_present`. Accepted normalized statuses are
`CLASSIFIED`, `REVIEWED`, `FAILED`, `PENDING`, and `NOT_OBSERVED`. `PENDING` and
`FAILED` can come from a sanitized event/Trust Center reconciliation; the
Account Usage `DATA_CLASSIFICATION_LATEST.STATUS` field itself reports
`CLASSIFIED` or `REVIEWED`.

Policy rows contain `asset_key`, opaque `policy_key`, `policy_kind`, assignment
(`DIRECT` or `TAG`), and Snowflake `policy_status`. Aggregation rows additionally
carry sorted `entity_key_hashes` so the analyzer can apply the entity-key
precedence exception without receiving column names.

POLICY_CONTEXT rows contain an opaque scenario, pass/fail/error status,
simulation timestamp, and the policy kinds exercised. A scenario proves only
the declared context and policy kinds; it does not replace inventory coverage.

## Receipt integrity

Each required receipt key is named exactly `denominator`, `tag_references`,
`policy_references`, or `classification_latest`. The object contains:

```json
{
  "schema_version": "1",
  "surface": "tag_references",
  "status": "COLLECTED",
  "collected_at": "2026-08-31T11:00:00Z",
  "row_count": 42,
  "truncated": false,
  "privilege_scope": "COMPLETE",
  "source": "SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES",
  "query_sha256": "sha256:<64 lowercase hex>",
  "receipt_sha256": "sha256:<64 lowercase hex>"
}
```

Compute `receipt_sha256` over canonical JSON of the receipt excluding the
`receipt_sha256` field: UTF-8, sorted keys, no insignificant whitespace, and
`ensure_ascii=false`. `COMPLETE` is an operator assertion supported by the role
and scope record retained outside the public artifact. Use `PARTIAL` or
`UNKNOWN` when visibility cannot be proved; the analyzer intentionally blocks.

The bundled collector also binds `template_sha256`, `rendered_sql_sha256`,
`dataset_sha256`, `row_count`, the exact source, privacy-safe selector metadata,
and a selector fingerprint. The analyzer recomputes every binding it can from
the installed template and matching rows. Do not hand-edit or copy a receipt to
a different dataset.

The input rejects raw `database_name`, `schema_name`, `table_name`,
`column_name`, `object_name`, `tag_value`, `policy_body`, `query_text`, and
`sql_text` fields. Retain those only in the approved restricted collection
workspace when operationally required.
