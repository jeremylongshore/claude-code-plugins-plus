# Snowflake read-only evidence collection

This directory is the model-neutral collection layer used by the Snowflake
operator skills. It executes reviewed, bounded SQL through an existing Snowflake
CLI connection profile and writes a source-stamped JSON envelope. It does not own
authentication, accept credential flags, or mutate Snowflake.

```bash
python3 shared/evidence/collect_snowflake_evidence.py \
  --surface query \
  --connection readonly-observer \
  --output ./snowflake-query-evidence.json
```

Baseline surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`data-quality`, and `replication`. The cost skill also bundles independently
receipted `cost-adaptive`, `cost-ai-functions`, `cost-budgets`,
`cost-internal-transfer`, `cost-resource-monitors`, `cost-storage`, and
`cost-transfer` surfaces. Each query is capped and intentionally collects
metadata rather than SQL text, raw failed rows, credential values, or customer
payloads. `row_limit` and `truncation_possible` in every receipt expose the reviewed
cap; a receipt at the cap is partial until a narrower query or pagination proves
completeness.

The access and auth surfaces have explicit current-state companions:
`access-current` (`SHOW GRANTS ON ACCOUNT`), `access-future` (a validated database
identifier), and `auth-current` (`SHOW USERS`). These operator-scoped snapshots must
be reconciled with Account Usage history; current/history disagreement blocks absence
and completeness claims. Account Usage `ROLES` and `LOGIN_HISTORY` are historical
and may lag by up to 120 minutes, so retain collection timestamps and source views.

Query and cost surfaces never export raw `USER_NAME` or `QUERY_TAG`. They emit
Snowflake-side `user_name_sha256`/`query_tag_sha256` values and
`query_tag_present` instead. Offline evidence must use the same pseudonymized fields;
raw identity or tag fields are rejected.

The `cost` and `query` surfaces include `WAREHOUSE_LOAD_HISTORY` rows so queue
pressure can be reconciled with attribution and query latency. Operator statistics
(`GET_QUERY_OPERATOR_STATS`) and `QUERY_INSIGHTS` are selector-gated sub-surfaces:

```bash
python3 shared/evidence/collect_snowflake_evidence.py --surface query-operator-stats \
  --query-id 01example --connection readonly-observer
python3 shared/evidence/collect_snowflake_evidence.py --surface query-insights \
  --query-id 01example --connection readonly-observer
```

Query IDs and database identifiers are opaque validated values, never SQL fragments.
Operator statistics require a completed query and the platform retrieval window;
Query History can lag by up to 45 minutes and Query Insights by up to 90 minutes.
Their receipts remain separately scoped and must match the target query. Likewise, pipeline `SYSTEM$PIPE_STATUS`
is collected only for an explicitly named pipe by the operator and is never replayed.

Reliability analyzers use separate near-live receipts: `pipeline-current`,
`data-quality-current`, and `replication-current`. The SHOW-based templates use
Snowflake's pipe operator so raw SHOW result sets never cross the collection boundary;
only the reviewed `EVIDENCE` projection is emitted. History and current-state receipts
must both verify, remain below their caps, and reconcile before an analyzer can claim a
complete graph, monitoring denominator, or failover-ready state.

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
datasets, row count, sanitized errors, and explicit non-claims. The domain skill
still decides whether the evidence is complete and fresh enough for its job.

## Bundle integrity

`collect_snowflake_evidence.py` and the SQL files in `shared/evidence/` are the
canonical sources. Each skill bundles a physical copy of that collector and its
reviewed SQL template so an installed skill remains self-contained. Check the
eight copies with:

```bash
python3 shared/evidence/sync_bundled_collectors.py --check
```

An explicit regeneration uses `--write`; it refuses unexpected skills, SQL
templates, symlinks, or other packaging-shape drift, and verifies byte parity
after writing. The collector receipt's `sql_sha256` continues to identify the
exact reviewed template used by a bundled copy.
