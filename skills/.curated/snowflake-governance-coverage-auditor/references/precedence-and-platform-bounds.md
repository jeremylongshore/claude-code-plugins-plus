# Precedence and platform bounds

## Effective versus present

A sensitive asset can have a tag and still have no effective policy. Count a
control only when its policy association is visible, its `POLICY_STATUS` is
`ACTIVE`, its platform feature is available, and precedence resolution leaves
it effective. Metadata visibility and a runtime simulation remain separate
proofs.

Snowflake documents these non-active statuses for policy references:

- `MULTIPLE_MASKING_POLICY_ASSIGNED_TO_THE_COLUMN`
- `COLUMN_IS_MISSING_FOR_SECONDARY_ARG`
- `COLUMN_DATATYPE_MISMATCH_FOR_SECONDARY_ARG`

Each is a configuration problem, not coverage.

## Direct and tag-based assignment

For the same policy type, a policy assigned directly to an object takes
precedence over a tag-based policy. Aggregation policies have a specific
exception: direct precedence applies when entity keys match; if entity keys
differ, both policies are enforced. Preserve hashed entity-key sets so an audit
does not flatten that distinction.

This rule is evaluated separately for masking, row-access, projection, join,
and aggregation controls. Different policy types can apply cumulatively.

## Edition and preview

Sensitive data classification requires Enterprise Edition or higher. Current
Snowflake documentation also marks tag-based aggregation, row-access,
projection, and join policies as open preview features available to Enterprise
Edition or higher. The analyzer therefore requires both an Enterprise-or-higher
edition and explicit preview-enable evidence before it counts those tag-based
associations.

Do not infer enablement from a catalog row. A replicated, dangling, stale, or
privilege-filtered reference is not runtime capability proof.

## Privilege visibility

The Account Usage `TAG_REFERENCES` view shows only objects visible to the
current role and contains direct references, not inherited tags. The Information
Schema functions can resolve current object-scoped references but are also
privilege filtered. `POLICY_REFERENCES` can return only a subset of associations
or no rows when the operator lacks relevant `APPLY` or `OWNERSHIP` privileges.

Accordingly, a zero-row result is never enough for an absence claim. Record the
collector role and bounded object scope outside the public bundle, then mark the
sanitized receipt `COMPLETE`, `PARTIAL`, or `UNKNOWN`.

## Latency

Account Usage `TAG_REFERENCES` and `POLICY_REFERENCES` can lag by two hours.
`DATA_CLASSIFICATION_LATEST` can lag by three hours. The denominator based on
Account Usage `COLUMNS` can lag by 90 minutes and can expose less information
than expected under some privilege arrangements. Set freshness bounds no tighter
than the source can support, and use current Information Schema evidence when a
decision cannot tolerate Account Usage latency.
