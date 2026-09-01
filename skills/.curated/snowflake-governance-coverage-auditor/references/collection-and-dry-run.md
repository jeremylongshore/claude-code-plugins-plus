# Collection and POLICY_CONTEXT dry-run

## Collection

`scripts/collect_governance_evidence.py` is the supported render/execute/seal
path for the templates under `scripts/sql/`, which are deliberately bounded and
read-only. Replace substitution tokens only through a trusted operator workflow:

- `__DATABASE_LITERAL__` is a validated string literal used only to narrow an
  Account Usage scan.
- `__ROW_LIMIT_PLUS_ONE__` is a positive integer one greater than the accepted
  output bound. If the extra row is returned, discard the export, partition the
  scope, and set `truncated: true` for the failed attempt.

The templates output hashes for object, tag, and policy identities. They do not
select tag values, policy bodies, comments, classification results, error text,
or data values. Retain raw Snowflake results only in the approved restricted
workspace; feed the analyzer the sanitized projection.

`TAG_REFERENCES` Account Usage evidence is direct-only. For inherited tags or
object-current confirmation, run the Information Schema `TAG_REFERENCES` or
`TAG_REFERENCES_ALL_COLUMNS` function for each bounded object and project the
same opaque keys. Do not call a catalog-wide loop without a fixed denominator
and row cap.

Join-policy attachments require current object-scoped Information Schema
`POLICY_REFERENCES` evidence because the Account Usage policy-reference view's
documented support list does not include join policies. A join policy catalog
row alone proves existence, not attachment.

Provide a restricted `--object-manifest` containing only `asset_key`,
`object_name`, and `domain` for those calls. The manifest may contain raw object
names, so keep it outside the distributable analyzer bundle. The collector
renders one bounded query per object, emits only opaque identities, records only
the object count in selector metadata, and binds the raw selector set by hash.

## Classification reconciliation

`DATA_CLASSIFICATION_LATEST` provides the last result per table. Its `STATUS`
is `CLASSIFIED` or `REVIEWED`; a later `LAST_CLASSIFICATION_ATTEMPT` than
`LAST_CLASSIFIED_ON`, with an error present, indicates that the latest attempt
failed. Export only an `error_present` boolean. Do not export the error message,
classification result payload, or tag values.

A table-level latest-classification row does not by itself prove that every
sensitive column has a current semantic category or tag. Derive column evidence
from the restricted classification result in the collection workspace, export
only the mapped opaque asset key and normalized state, and keep the raw result
out of the analyzer bundle.

Trust Center and event-table evidence may supply a normalized `FAILED` or
`PENDING` state. A failure can be delayed before retry, including timeout cases
tied to the classification profile's maximum validity schedule. Pending and
retry states must never be labeled current coverage.

## POLICY_CONTEXT dry-run

`POLICY_CONTEXT` simulates how masking, row-access, aggregation, join, and
projection policies affect a query under supplied context values. It does not
mutate policy state. It can nevertheless expose protected data if the query is
careless, so this skill does not generate a universal query.

For each scenario:

1. Have the policy owner define the exact role/context and expected invariant.
2. Use a query that returns only a boolean or bounded aggregate assertion. Do
   not select protected rows or values into an audit artifact.
3. Run under a role that already has the documented `OWNERSHIP` on the table or
   view plus the relevant account-level or policy-level `APPLY` privilege.
4. Record only opaque asset/scenario keys, policy kinds, timestamp, and
   `PASS`, `FAIL`, or `ERROR`.
5. Treat errors, missing privilege, unsupported sharing context, stale results,
   or an incomplete role hierarchy as `NOT_PROVEN`. Do not switch to
   `ACCOUNTADMIN` automatically.

Simulate positive and negative contexts when the policy condition varies by
role, user, activated roles, account, or other supported context. The report
requires one fresh passing scenario that covers all required policy kinds for
each controlled denominator asset; teams may impose a stricter scenario matrix.

## Dry-run remediation packet

The analyzer identifies the opaque asset, reason codes, required metadata
refresh, and policy-context precheck. It intentionally emits no SQL. A separate
change workflow must resolve the real object identity, choose the policy/tag or
classification operation, obtain approval, verify positive and negative
behavior, and retain rollback evidence.
