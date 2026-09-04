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

Baseline surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`auth-login-history`, `data-quality`, and `replication`. Failover evidence also
has `replication-current`, `replication-progress`, and
`replication-dangling`. Access has narrowly
scoped `access-*` sub-surfaces for the current session, grants to/of a role, user
grants, database-role grants, and paired database/schema future grants. The cost
skill also bundles independently
receipted `cost-adaptive`, `cost-ai-functions`, `cost-budgets`,
`cost-internal-transfer`, `cost-resource-monitors`, `cost-storage`, and
`cost-transfer` surfaces. Each query is capped and intentionally collects
metadata rather than SQL text, raw failed rows, credential values, or customer
payloads. `row_limit` and `truncation_possible` in every receipt expose the reviewed
cap; a receipt at the cap is partial until a narrower query or pagination proves
completeness.

Native App provider evidence uses three selector-bound current surfaces:
`native-app-versions-current`, `native-app-release-directives-current`, and
`native-app-upgrade-cohorts-current`. Each requires one strict unquoted
`--application-package`, emits only Snowflake-side scoped hashes and allowlisted
state/version fields, and binds the receipt's rendered SQL to the
Snowflake-produced package hash. Error receipts retain template proof only.
`APPLICATION_STATE` is a provider-side current snapshot with documented latency
up to 10 minutes and no retention after uninstall; lifecycle completeness must
come from separate trusted evidence. All three cap their data dataset at 5,000
rows and a cap hit blocks release claims.

Governance coverage uses three selector-bound current surfaces:
`governance-classification-current`, `governance-tags-current`, and
`governance-policies-current`. They bind database/object/domain selectors to
Snowflake-produced hashes and preserve classification latency, visibility, and
profile-state limits. `POLICY_CONTEXT` is deliberately outside this collector:
its `EXECUTE USING` form must remain a separately trusted, sanitized simulation
receipt and never weakens the collector's global read-only SQL guard.

Pipeline evidence is live-only schema 2 and intentionally split across six
single-statement surfaces. `pipeline` requires an explicit half-open UTC window
of at most seven days and independently caps task, dynamic-table refresh, and
copy history at 5,000 rows. Settlement is based on task completion, non-executing
refresh end, and copy completion—not schedule/start time. `pipeline-task-current`,
`pipeline-stream-current`, `pipeline-dynamic-table-current`, and
`pipeline-pipe-current` collect role-visible current inventories with a 10,000
object cap. `pipeline-pipe-status` accepts one strictly validated three-part
pipe selector and returns only allowlisted state/count/timestamp fields. It
never serializes raw pipe-status JSON, file paths, notification channels, or
free-text errors. The pipeline analyzer requires exact receipt and row schemas,
matching authorization contexts, an explicit evaluation timestamp, current
observations no older than 15 minutes, and a separately recorded whole-bundle
digest. It binds safe history-window selectors to rendered SQL and each pipe
selector to a privacy-bound rendered-SQL digest derived from its scoped object
hash. All admitted text values use finite documented domains; raw schedule,
target-lag, reason-code, and provider-message strings are omitted. It keeps bounded evidence completeness
separate from dependency-graph completeness and account-wide visibility.

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
`SNOWFLAKE_SERVICE` rows remain in raw cap accounting but carry an explicit
excluded scope marker; operator-owned `SERVICE_AGENT` rows remain in scope.

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
does not guess an ID or broaden privileges. Pipeline `SYSTEM$PIPE_STATUS` is
queried only through the named, privacy-projected `pipeline-pipe-status` surface;
raw JSON is never retained and no pipe operation is executed.

Data-quality evidence is live-only schema 2 and split across four independently
receipted surfaces. `data-quality` requires an explicit half-open UTC window of
at most seven days and collects only expectation outcomes and timestamps from
`SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS`; Snowflake publishes
no latency SLA for that local history, so the receipt declares no settlement.
`data-quality-associations-current` and
`data-quality-expectations-current`, like `data-quality-notification-current`,
require a strictly validated unquoted three-part `--data-quality-object` and
`--data-quality-domain TABLE|VIEW`. Each queries the selected object's
database-scoped Information Schema table function with a 5,000-row cap and an
uncapped same-statement source count. Snowflake publishes no latency SLA for
these live functions; each receipt is a role-filtered observation at
`observed_at`, not a freshness or completeness guarantee. The receipt retains
only the selected-object hash/domain and binds its rendered-SQL digest to that
Snowflake-produced context; an error receipt retains only public template proof
and no selector fingerprint. Raw object, metric, role, schedule, filter,
grouping, expectation, and expression values are never emitted.
The cross-surface metric hash is name-scoped because the local history does not
expose the same signature representation as both live functions; the scoped
association hash (`REF_ID`/`REFERENCE_ID`) binds the exact applied overload.

The notification surface emits only finite notification state plus scoped
object/association/metric hashes. All three selector-scoped current surfaces
retain selected-object hash/domain in same-statement execution context even at
zero rows. Current inventories and
bounded history remain observations: they do not prove policy enforcement,
notification delivery, denominator completeness, or a passing quality outcome.

Failover evidence is live-only schema 2. `replication-current` privacy-projects
role-visible `SHOW FAILOVER GROUPS` rows and records the calling account context.
`replication` and `replication-progress` require explicit half-open UTC windows of
at most seven days against the target account's Information Schema functions;
Snowflake documents 14-day retention but no numeric visibility-latency SLA for
those functions. `replication-dangling` requires one validated local group
selector and hashes the selector and every entity identifier inside Snowflake.
The analyzer requires exact source/target scope coverage, one uncapped receipt per
required scope, current observations no older than 15 minutes, independently
recorded bundle/policy/operator digests, exact policy denominators, paired
history/progress windows ending within 60 seconds of collection start and 15
minutes of evaluation, and matching
authorization contexts per account. Full drills require history/progress proof in
both directions. RPO uses only the latest uniquely completed job's
`PRIMARY_SNAPSHOT_TIMESTAMP` before each decision point. The SQL
allowlist rejects unreviewed `SYSTEM$` functions so refresh, cancellation, and
other control-plane actions cannot enter the collection path.
For query-forensics completeness, preserve the anchor row's `role_name` and the exact
query-history source. The analyzer rejects role/source mismatches, applies terminal
statuses only to their matching surface, and requires at least one bound operator row.

Run each supplemental cost surface separately and retain all receipts beside the
normalized evidence. The cost analyzer accepts them under `supplemental_receipts`
and verifies the exact template, source, payload, collection time, and canonical
receipt hash. A surface-inventory row without its matching receipt cannot support a
complete cost claim.

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
