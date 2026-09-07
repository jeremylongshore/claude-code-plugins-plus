# Cost evidence output contract

The report must remain useful to finance and engineering without overstating what the
usage views prove.

## Required header

```text
Account / account locator
Role used for collection
Identity disclosure authorization and authority
Session UTC offset
UTC half-open analysis window
Source-specific settled cutoff
Same-statement settlement observation and collection-completion timestamp
Maximum timestamp returned by each source
Collection query ID, or the explicit reviewed-transport unavailable marker, plus the
reviewed SQL hash, result hash, row count, and cap state
Included surfaces
Unavailable or excluded surfaces
Invoice reconciliation status
```

## Required sections

### Typed cost ledger

For every entry include the domain, source, role, native unit, amount, parent ID,
overlap key, aggregation eligibility, freshness, availability, and invoice status.
Only `total` entries are additive without separate invoice evidence. Query and AI
detail remain `attribution`; storage byte-days and transfer bytes remain `context`; currency
conversions remain `estimate`. Adaptive compute attribution must use compute credits,
not total credits containing cloud services. Snowflake's general
[service-type taxonomy](https://docs.snowflake.com/en/sql-reference/service-types)
labels Cortex AI Functions usage `AI_FUNCTIONS`, but
[`METERING_HISTORY`](https://docs.snowflake.com/en/sql-reference/account-usage/metering_history)
exposes the broader `AI_SERVICES` total. Attach detail beneath an account/window-aligned
`AI_SERVICES` row when one exists, without asserting equality because that service type
also covers Cortex Analyst; otherwise leave the parent relationship unknown.

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

Use the fixed latency matrix in
[cost-ledger-and-surfaces.md](cost-ledger-and-surfaces.md), not a caller-supplied
threshold. Maximum returned timestamps describe activity, not ingestion health; a
quiet surface is not stale merely because it has no recent row. State whether each
window end precedes its fixed settled cutoff, computed from
`execution_context.observed_at` rather than CLI completion, and whether in-progress
Adaptive or AI rows were excluded from final evidence.

Include both the baseline collector assessment and every expected supplemental
receipt assessment. A complete claim requires the exact reviewed template hash,
canonical receipt hash, expected source, normalized payload match, timestamp, and cap
for each supplemental surface in scope.

The receipt proves local self-consistency only. Its self-checksum does not authenticate
Snowflake, the connection, or the collector, and fields absent from the reviewed SQL
cannot prove latency, budget coverage, monitor enforcement, or invoice reconciliation.

### Storage dimensionality

Report `STORAGE_USAGE` values as daily average-byte snapshots. This analyzer multiplies
each average by its non-overlapping interval duration and reports the sum as
`byte-days`. Never sum multiple daily snapshots and label the result `bytes`. State that Snowflake documents
different measurement semantics from invoice storage. See
[STORAGE_USAGE](https://docs.snowflake.com/en/sql-reference/account-usage/storage_usage).

### Identity disclosure

Report whether raw identity disclosure was authorized and name the authority when it
was. The authorization marker and authority are part of the trusted input digest. If
authorization is false, the account, role, review owner, and approval boundary must be
lowercase 64-hex scoped digests; do not render raw values.

### Billing and invoice evidence

Label the evidence level explicitly:

1. hourly operational usage, before the daily cloud-services adjustment;
2. daily cloud-adjusted billed credits from
   [`METERING_DAILY_HISTORY`](https://docs.snowflake.com/en/sql-reference/account-usage/metering_daily_history);
3. organization-currency usage-statement evidence from
   [`USAGE_IN_CURRENCY_DAILY`](https://docs.snowflake.com/en/sql-reference/organization-usage/usage_in_currency_daily),
   optionally corroborated by
   [`RATE_SHEET_DAILY`](https://docs.snowflake.com/en/sql-reference/organization-usage/rate_sheet_daily).

Organization billing rows are delayed and mutable until month close, and the invoice
or issued usage statement remains authoritative. Never promote a customer-supplied
rate or statement row to reconciled merely because its local receipt hash matches.

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
- Query-tag coverage is limited to the collected attribution surface; it is not
  account-wide ownership coverage.
- AI Functions evidence is not exhaustive Cortex/AI cost coverage.
- Visible monitor or budget inventory does not prove enforcement, notification,
  linked-resource, account-root-budget, or account-wide coverage.
- A receipt self-checksum is not proof of Snowflake origin or authenticity.

## Redaction

Do not include raw query text or IDs, credentials, tokens, connection profiles or
paths, environment values, notification addresses, contract numbers, raw warehouse or
model names, raw user names, or raw query tags.
Hash customer-controlled warehouse, compute-pool, budget, owner, model, and account
display names unless explicitly authorized for the report. Prefer a stable
organization-and-account-scoped pseudonym and retain any mapping outside the report.
