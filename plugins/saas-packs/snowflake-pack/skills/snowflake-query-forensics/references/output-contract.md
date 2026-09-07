# Query forensics output contract

## Schema transition

Pack `3.x` is an explicit breaking transition. The analyzer accepts normalized input
schema `2.0`, requires query collector receipt schema `2`, and emits output schema `2.0`.
Legacy inputs without `schema_version: "2.0"` must be recollected or migrated; do not
silently interpret them under the stricter identity and freshness contract.
Pack `2.1` automation that relied on the receipt self-checksum as verification must
also add the trusted-boundary digest workflow described below. Without that external
boundary, schema `2.0` analysis is explicitly untrusted and cannot make confirmed or
completeness claims.

## Header

Record:

- account, role, warehouse, query ID, execution state;
- query hash and parameterized hash when available;
- history surface, receipt-bound source maximum timestamp, collection time, declared
  maximum source age, and resulting `FRESH`/`STALE`/`UNVERIFIED` status;
- operator-stat and Query Insights availability;
- `BOUND`/`INCOMPLETE` evidence-binding status for the anchor query ID;
- redaction applied.

## Timeline

Report supplied timing fields without a universal threshold:

```text
total elapsed
compilation
execution
queue overload
queue provisioning
queue repair
transaction blocked
other/unexplained if the supplied fields do not reconcile
```

Do not fabricate zeroes for missing fields.

## Trust, cap, and anchor freshness

`receipt_sha256` is a self-checksum. It establishes internal content consistency only:
it is not a signature, MAC, collector identity, or proof of origin, because an attacker
who replaces the data can recompute the checksum. The analyzer reports a consistent
but unanchored receipt as `self_consistent_untrusted` and withholds confirmed,
freshness, completeness, operator, comparison, and ROI claims.

To authorize those claims, assemble the final normalized schema `2.0` bundle inside a
trusted local collection boundary and record its canonical digest separately:

```bash
python3 scripts/analyze_query_evidence.py \
  --input normalized-query-evidence.json \
  --print-input-sha256 > normalized-query-evidence.sha256
```

Transport or store the digest independently, then analyze with
`--trusted-input-sha256 sha256:<hex>`. A match proves only that the canonical bundle is
unchanged since that trusted boundary. It does not authenticate a person or collector
and provides no cryptographic authenticity without a secret/signature trust root.
Computing the digest from the same untrusted file being analyzed creates no trust.

The analyzer derives the reviewed cap directly from bundled `query.sql`. Receipt
`row_limit` must equal it, `truncation_possible` must match the row count, and any cap
hit is incomplete. Rehashing a changed cap cannot bypass this contract.

Receipt trust also binds semantic identity. `metadata.history_source` must equal the
receipted query-history source, and `metadata.role` must equal the anchor row's
`role_name`. A matching bundle digest does not excuse either mismatch.

Receipt `dataset_max_time` is the latest timestamp across every query-history row and
is informational. `metadata.history_source_max_time` must equal the latest timestamp
on the receipt row whose UUID matches the anchor query ID. The analyzer repeats both
derivations, so an unrelated newer row cannot make an old anchor fresh.

Account Usage terminal values are `success`, `fail`, and `incident`; Information
Schema terminal values include `success`, `failed_with_error`, and
`failed_with_incident`. Treat unknown values and running, queued, blocked, or warehouse
resumption states as nonterminal. Apply those sets only to their matching receipted
surface. A nonterminal packet is always incomplete and emits no confirmed observations,
even when operator and insight arrays are empty. A terminal packet requires at least one
bound operator row for `evidence_binding: BOUND`; missing operator JSON produces a
history-only partial packet. Query Insights may be absent, but that absence remains
unknown coverage rather than evidence of health.

Before serializing JSON or Markdown, recursively redact credential-bearing and
raw-SQL-like scalar values. Authorization classification must consume the complete folded
value for every syntactically valid scheme when an Authorization header supplies the
context. Outside a header, redact only when a standardized scheme is followed by
credential evidence: token padding/digits/punctuation, an unknown token-like value in
credential position, or a recognized sensitive parameter parsed with the complete token-name
grammar. Registered SCRAM-SHA-1 and SCRAM-SHA-256 schemes share this boundary. Ambiguous
known capability/status prose such as `Basic authentication`, `Bearer
support`, `DPoP enabled`, and `Mutual authentication` remains visible; this headerless
boundary does not claim to identify every possible alphabetic token68 value. Also preserve
`OAuth flow-reviewed`, `Signature algorithm=RSA was reviewed`, `Token count`, and `Request
id=3,response=200`. Detect raw SQL by stripping
chained diagnostic/statement labels, empty leading statements, and comments without crossing quoted
values, then tokenizing the candidate and validating its statement-family grammar,
including positional/named binds, quoted file URIs, arbitrary integration subtypes,
object modifiers, and scripting blocks driven by the shared recognized statement-verb
family; do not accumulate value-shape regex examples. Use expression and sentence
continuation grammar—not table-name word exceptions—to preserve prose such as `Values
(count,total), not rates...` and `Select (operator) from the plan...`. Normalize sensitive
keys across snake, kebab, camel, and case
variants before deciding whether to reject or redact them. Treat `hasPassword`, `has_pat`,
`hasRsaPublicKey`, and `has-workload-identity` as safe metadata only when the value is an
actual boolean; redact or reject every other value type. Reject unsafe operator IDs/types
and experiment-owner values under bounded grammars; preserve safe evidence text.

## Confirmed observations

List raw positive evidence: wait time, spill bytes, operator-time percentage, platform
insight, errors, and other supplied counters. Name the exact source.

## Estimated or derived metrics

List ratios separately:

- output rows / input rows;
- partitions scanned / partitions total;
- before/after change if the comparison inputs are aligned.

Derived does not mean incorrect; it means the value was computed rather than directly
reported.

## At-risk hypotheses

Every hypothesis needs:

- evidence;
- competing explanation;
- next read-only check;
- evidence that would falsify it;
- owner for any later experiment.

## One-variable experiment

If the user wants remediation, propose only one variable at a time. State baseline,
change, fixed inputs, measurement window, success criteria supplied by the user, impact,
approval, and rollback. Do not execute the experiment.

## Required non-claims

- No single metric was treated as a proven root cause.
- No universal performance threshold or SLA was applied.
- No SQL, warehouse, clustering, session, or query state was mutated.
- Raw query text was not required by the evidence contract.

## Good conclusion

> Query `01...` recorded remote spill on operator 7 and spent the largest reported
> operator-time share there. Query-shape and capacity pressure remain competing causes.
> Compare the same parameterized hash over an aligned data window before approving a
> one-variable experiment.

## Bad conclusion

> The warehouse is too small; resize it to Large.

The bad conclusion invents the root cause, target size, and authorization.
