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

Top-level surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`auth-login-history`,
`data-quality`, and `replication`. Access also has narrowly scoped `access-*`
sub-surfaces for the current session, grants to/of a role, user grants, database-
role grants, and paired database/schema future grants. Each query is bounded and intentionally collects
metadata rather than SQL text, raw failed rows, credential values, or customer
payloads. `row_limit` and `truncation_possible` in every receipt expose the reviewed
cap; a receipt at the cap is partial until a narrower query or pagination proves
completeness.

Current access sub-surfaces are live-only. Each scoped `SHOW` uses Snowflake's
pipe operator to project allowlisted grant columns and exactly one execution
context row in the same statement. The analyzer compares authorization-context
fingerprints across independent invocations; matching profile names alone are
not evidence, and different session IDs are never described as one session.

Authentication evidence is also live-only and split deliberately across three
independent caps: `auth-current` for privacy-projected `SHOW USERS`, `auth` for
delayed Account Usage `USERS`, and `auth-login-history` for the settled portion
of a trailing seven-day horizon
that excludes the newest 120 minutes. Each emits the same pseudonymous execution-
context fields. Raw usernames and event IDs never leave Snowflake. The auth
analyzer requires all three exact schema-2 receipts plus an out-of-band whole-
bundle digest; SHOW flags and LOGIN_HISTORY observations never prove canary
causality, effective policy, old-path denial, recovery, or account-wide absence.
The authorization fingerprint hashes organization name plus account name rather
than the reusable legacy account locator. `REPORTED_CLIENT_TYPE` is never
collected because it is unauthenticated telemetry. Snowflake-managed
`SNOWFLAKE_SERVICE` rows are excluded from both user surfaces; operator-owned
`SERVICE_AGENT` rows remain in scope.

Access receipt schema `2` additionally binds each scoped `SHOW` collection to
its canonical template hash, rendered SQL hash, selector fingerprint, expected
datasets, exact per-dataset counts, and selector-presence metadata. Dynamic SQL
is written with mode `0600` outside the package and removed on success, CLI
failure, timeout, malformed output, or unexpected runner error. The receipt does
not expose the selector value. The access analyzer recomputes every binding from
the schema `2.0` bundle and blocks completeness unless the whole bundle matches
a separately recorded digest. A match is an operator assertion of byte identity,
not authentication or provenance.

The access baseline uses `SNOWFLAKE.SECURITY_VIEWER` and can lag by up to 120
minutes. Current `SHOW` output is limited by the executing primary role. Full
visibility requires `MANAGE GRANTS`, which can mutate authorization; the
collector never grants it, switches to `ACCOUNTADMIN`, or changes primary or
secondary roles. A database future receipt without its relevant schema receipt
cannot support a precedence claim.

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

Live CLI error receipts never persist free-form stdout or stderr. They contain a
bounded error code, exit code, and generic local-diagnostics message. The
deterministic scalar sanitizer remains a defense for explicitly constructed
error envelopes, but it is not treated as proof that arbitrary provider text is
safe to serialize. Credential-adjacent `has_*` fields pass only when their
values are actual booleans.

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

## Bundle integrity

`collect_snowflake_evidence.py` and the SQL files in `shared/evidence/` are the
canonical sources. Each registered skill bundles physical copies so it remains
self-contained when installed without the rest of the pack. From the pack root,
check all eight projections without changing the tree:

```bash
python3 shared/evidence/sync_bundled_collectors.py --check
```

After reviewing a canonical collector or SQL change, regenerate the registered
copies explicitly:

```bash
python3 shared/evidence/sync_bundled_collectors.py --write
```

Regeneration refuses missing skill structure, unregistered shared-collector
copies, orphan templates, symlinks, and unexpected destination files. It writes
only registered collector and SQL files in a pre-staged transaction, rolls the
complete projection set back if a replacement fails, preserves canonical
modes, and verifies SHA-256 parity afterward. Receipt `sql_sha256` values bind
execution to the same canonical template content; generated selectors also have
a separate rendered hash and opaque fingerprint. They are integrity metadata,
not proof of origin.
