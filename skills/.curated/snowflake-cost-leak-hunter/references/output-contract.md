# Cost evidence output contract

The report must remain useful to finance and engineering without overstating what the
usage views prove.

## Required header

```text
Account / account locator
Role used for collection
UTC half-open analysis window
Collection timestamp
Maximum timestamp returned by each source
Included surfaces
Unavailable or excluded surfaces
Invoice reconciliation status
```

## Required sections

### Typed cost ledger

For every entry include the domain, source, role, native unit, amount, parent ID,
overlap key, aggregation eligibility, freshness, availability, and invoice status.
Only `total` entries are additive without separate invoice evidence. Query and AI
detail remain `attribution`; storage and transfer bytes remain `context`; currency
conversions remain `estimate`.

### Confirmed observations

List observed credits by source and category. “Confirmed” means confirmed in the
supplied Snowflake evidence, not confirmed billed dollars.

### Estimated amounts

Show this section only when an applicable rate-card entry was supplied. Include
currency, unit rate, provenance, effective period when known, and invoice-reconciliation
status. Do not add amounts in different currencies.

### At-risk opportunities

Rank by observed credits without applying an invented severity threshold. Every row
must include:

- evidence and calculation;
- why it is only at risk;
- competing explanation;
- next read-only verification;
- change owner and approval boundary.

### Coverage and freshness

List actual source ages and the official latency/coverage caveats checked during the
run. “No rows” must be distinguishable from “surface unavailable,” “region
unavailable,” “privilege error,” and “collection truncated.”

Include both the baseline collector assessment and every expected supplemental
receipt assessment. A complete claim requires the exact reviewed template hash,
canonical receipt hash, expected source, normalized payload match, timestamp, and cap
for each supplemental surface in scope.

### Approval queue

Write proposed configuration changes separately. Do not execute them. Include impact,
verification, and rollback for later operator review.

## Headline rules

Good:

> The supplied window contains 42.5 confirmed warehouse compute credits. Of those,
> 11.2 credits are unattributed to query execution and require workload-owner review.

Good with supplied rate:

> Using the customer-supplied rate-card row effective for this warehouse category,
> 42.5 credits convert to an estimated 125.38 USD. This is not invoice-reconciled.

Bad:

> Snowflake is wasting $125/month.

The bad form invents recoverability, cadence, and invoice truth.

## Required non-claims

- Credits are not reconciled invoice amounts.
- At-risk credits are not promised savings.
- No warehouse size, threshold, price, or SLA was inferred.
- No Snowflake object or configuration was mutated.

## Redaction

Do not include raw query text, credentials, tokens, connection paths, or environment
values. Include user names only if the report audience is authorized; otherwise replace
them with stable local pseudonyms and retain the mapping outside the report.
