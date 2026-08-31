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

Supported surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`data-quality`, and `replication`. Each query is capped and intentionally collects
metadata rather than SQL text, raw failed rows, credential values, or customer
payloads. `row_limit` and `truncation_possible` in every receipt expose the reviewed
cap; a receipt at the cap is partial until a narrower query or pagination proves
completeness.

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
