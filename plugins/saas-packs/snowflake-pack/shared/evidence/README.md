# Snowflake read-only evidence collection

This directory is the model-neutral collection layer used by the Snowflake
operator skills. It executes reviewed, bounded SQL through an existing Snowflake
CLI connection profile and writes a source-stamped JSON envelope. It does not own
authentication, accept credential flags, or mutate Snowflake.

```bash
python3 shared/evidence/collect_snowflake_evidence.py \
  --surface query \
  --connection readonly-observer \
  --source-max-age-seconds 2700 \
  --output ./snowflake-query-evidence.json
```

Supported surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`data-quality`, and `replication`. Each query is capped and intentionally collects
metadata rather than SQL text, raw failed rows, credential values, or customer
payloads. `row_limit` and `truncation_possible` in every receipt expose the reviewed
cap; a receipt at the cap is partial until a narrower query or pagination proves
completeness.

The query surface requires a positive incident freshness bound. Query receipt schema
`2` records the maximum visible query-history timestamp across all receipted rows as
`dataset_max_time`, the bound, and collection time. That dataset maximum is
informational: the query analyzer derives freshness from the latest timestamp on rows
whose UUID equals the anchor query ID. A newer unrelated row cannot freshen the anchor.

The embedded `receipt_sha256` is only a self-checksum over the receipt contents. It can
detect an accidental edit, but anyone able to replace the receipt can recompute it; it
does not prove origin, collector identity, or authenticity. Query-forensics treats a
self-consistent receipt as `self_consistent_untrusted` and blocks confirmed,
freshness, completeness, operator, comparison, and ROI claims unless the final
normalized bundle also matches an out-of-band digest recorded at a trusted local
boundary. That digest is not a signature or secret-backed MAC. Preserve it separately
from the evidence transport; computing it from the same untrusted copy creates no
trust.

Collector error receipts use the same deterministic scalar sanitizer as query-forensics
output: explicit Authorization and Proxy-Authorization headers consume any valid scheme and
complete value. Headerless credentials require evidence from a standardized scheme's token
shape/position or a recognized sensitive parameter using the complete token-name grammar;
registered SCRAM-SHA-1 and SCRAM-SHA-256 share the same family-safe classification.
known ambiguous capability/status words remain prose, so arbitrary alphabetic headerless
token68 is not claimed as complete coverage. Password/token tails, normalized sensitive-key variants, and tokenized Snowflake
statement families—including chained diagnostic labels, empty prefixes, positional/named
binds, quoted file URIs, arbitrary integration subtypes, modifiers, and scripting driven
by a shared statement-verb family—are removed
before receipt hashing or serialization. Ordinary authentication/OAuth status evidence,
request counters, and safe prose are preserved. Credential-adjacent `has_*` fields pass
only when their values are actual booleans.

The bundled query SQL emits analyzer field names directly, including the `_ms` timing
suffixes. Preserve those row objects exactly when mapping `datasets.query_history`
into normalized schema `2.0`; exact row equality is part of receipt validation. The
analyzer also reads the reviewed SQL `LIMIT` and requires `row_limit` and
`truncation_possible` to agree with that contract. A cap hit or any cap mismatch is
incomplete, even if the receipt self-checksum was recomputed.

Query and cost surfaces never export raw `USER_NAME` or `QUERY_TAG`. They emit
Snowflake-side `user_name_sha256`/`query_tag_sha256` values and
`query_tag_present` instead. Offline evidence must use the same pseudonymized fields;
raw identity or tag fields are rejected.

The `cost` and `query` surfaces include `WAREHOUSE_LOAD_HISTORY` rows so queue
pressure can be reconciled with attribution and query latency. Operator statistics
(`GET_QUERY_OPERATOR_STATS`) and `QUERY_INSIGHTS` require a concrete query ID and
are supplied as a separately redacted dataset to the domain analyzer; the collector
does not guess an ID or broaden privileges. Likewise, pipeline `SYSTEM$PIPE_STATUS`
is collected only for an explicitly named pipe by the operator and is never replayed.
For query-forensics completeness, preserve the anchor row's `role_name` and the exact
query-history source. The analyzer rejects role/source mismatches, applies terminal
statuses only to their matching surface, and requires at least one bound operator row.

The runner invokes only:

```text
snow sql --filename <reviewed-file> --connection <profile> \
  --format JSON_EXT --silent --enhanced-exit-codes --local-only
```

Configure the profile with Snowflake CLI using the organization's approved
authentication method. Never pass passwords, private keys, OAuth tokens, or MFA
codes to this collector. The selected profile must have only the read privileges
needed by the requested views. A permission failure is recorded as missing
evidence; it is not a reason to switch to `ACCOUNTADMIN`.

Every output includes the collection timestamp, SQL SHA-256, source views,
datasets, row count, sanitized errors, and explicit non-claims. These fields support
content-integrity checks; they do not authenticate the collector. The domain skill
still decides whether the evidence is trusted, complete, and fresh enough for its job.
