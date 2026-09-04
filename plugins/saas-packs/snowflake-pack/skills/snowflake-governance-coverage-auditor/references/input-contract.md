# Governance input contract

The analyzer accepts exactly `schema_version`, `policy`, `collector_receipts`,
`scope_receipt`, and `simulation_receipts`. The wrapper is schema `2`; the
owner-policy and attestation receipts are schema `1`.

The policy binds the analysis clock, organization/account hashes, known edition,
receipt and classification age thresholds, exact preview features, and exact
asset and scenario arrays. Each array has both a count and canonical SHA-256.
Each asset carries asset, object, database, and domain hashes; required tag-key
and key/value-binding hashes; required control enums; and exact scenario hashes.
Each scenario binds one asset/control pair to context, query-shape, and expected
outcome hashes.

The evidence digest covers the schema version, collector receipts, scope receipt,
and simulation receipts. The policy digest covers the policy alone. Record them
independently before evidence assembly; receipt self-checksums are only tamper
detection, not provenance.

Current collection requires exactly one classification receipt for every policy
database and one tag plus one policy receipt for every policy object. All
receipts must be live, under 130 seconds duration, no older than the policy's
maximum (at most 15 minutes), uncapped below 5,000 rows, selector-bound, and from
one identical hashed execution context.

The scope receipt must independently reconcile the exact database/object hashes,
all six policy kinds, and current classification/tag/object visibility for that
same context. It must also carry one sorted `ACTIVE`, `MISSING`, `DISABLED`, or
`UNKNOWN` classification-profile status for every policy database and attest that
profile scope was reviewed. Anything other than `ACTIVE` blocks bounded coverage.
The strict simulation receipt retains no result value or SQL; it binds only
approved hashes, a fixed outcome enum, time, context, and its operator-executed
source label.

Any missing, extra, duplicated, stale, malformed, raw-text, context-mismatched,
capped, or resealed-but-externally-untrusted input is rejected with a generic
error before findings are constructed.
