---
name: snowflake-data-quality-sentinel
description: |
  Assess Snowflake data metric function coverage and current quality evidence
  without reading customer rows. Use when expectations or anomaly monitoring may
  be violated, stale, suspended, incomplete, mis-scoped, or unavailable, or when
  an operator needs separate data-quality and monitoring verdicts. Trigger with
  "Snowflake data quality", "DMF expectation", "expectation violation",
  "anomaly training", "data quality monitoring gap", or "stale DMF result".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[normalized-evidence.json]"
model: inherit
effort: high
version: 3.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: "Model-neutral; requires Python 3.10+. Optional collection requires Snowflake CLI with an existing read-only profile."
tags: [saas, snowflake, data-quality, governance, observability, incident-response]
---

# Snowflake Data Quality Sentinel

## Overview

Turn the shared Snowflake `data-quality` evidence surface plus an
owner-approved requirement denominator into two independent verdicts:

- `quality_status`: what current valid results prove about the data.
- `monitoring_status`: whether the checks, schedules, roles, groups,
  notifications, and evidence sources are operating as required.

Never treat a missing result, anomaly training, or a raw metric without an
objective as healthy. Never inspect or request failed customer rows.

## Prerequisites

- Python 3.10+ for deterministic analysis.
- A normalized packet matching the linked input contract.
- For live collection only, Snowflake CLI with an existing least-privilege profile.

## Inputs

Use `Read` to inspect the evidence envelope and the contract in
[references/input-contract.md](references/input-contract.md). Required inputs are
requirements, observed associations, measurements, and source metadata. The
requirements are the denominator; discovered metrics do not silently enlarge it.

When live evidence is needed, use the shared read-only collector first:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface data-quality \
  --connection readonly-observer \
  --output ./snowflake-data-quality-evidence.json
```

Authentication belongs to that existing Snowflake CLI profile. Do not accept or
persist passwords, private keys, OAuth tokens, MFA codes, or temporary connection
flags. A permission or edition error is evidence, not authorization to switch to
`ACCOUNTADMIN`.

## Workflow

1. Confirm the input contains the declared requirement denominator and the shared
   collector receipt hash. Stop on raw failed rows, PII, credential fields, SQL
   text, or presigned URLs. If `truncation_possible` is true, narrow or partition
   the evidence window before issuing either verdict.
2. Run the deterministic analyzer with `Bash`:

   ```bash
   python3 scripts/analyze_data_quality.py <normalized-evidence.json> --pretty
   ```

3. Report `quality_status` and `monitoring_status` separately. Preserve every
   finding code, scope, evidence statement, and bounded action.
4. Point at the provenance receipt: input hash, collector receipt hash, evidence
   window, collection time, and source status. Do not turn a stale or unavailable
   source into a pass.
5. If remediation would mutate Snowflake, stop at a dry-run change packet and ask
   for explicit authorization under the caller's change process.

## Decision Rules

- Status precedence is `FAIL`, `DEGRADED`, `INCONCLUSIVE`, `PASS`, then
  `NO_REQUIRED_CHECKS`.
- `DQ_EXPECTATION_VIOLATED` and `DQ_ANOMALY_DETECTED` can fail data quality.
- Evaluation failure, missing/stale results, missing objectives, unsupported
  objects, edition boundaries, and source gaps make quality inconclusive.
- Association, role, notification, schedule, and group findings affect monitoring;
  they do not fabricate a data-quality violation.
- `DQ_ANOMALY_TRAINING` is never a pass.
- `DQ_METRIC_OBSERVED_NO_OBJECTIVE` is an observation only, never a violation.
- Enterprise data-quality unavailability is a bounded blocker. Record it and stop
  claims that depend on that surface.

## Output

Return the analyzer JSON or a concise rendering that preserves:

- both statuses and the exact requirement/association/measurement/source counts;
- deterministic finding codes and actions;
- provenance and receipt hashes;
- the four non-claims emitted by the analyzer.

An empty requirement denominator returns `NO_REQUIRED_CHECKS`; it does not mean
that discovered Snowflake objects are healthy.

## Example

```bash
python3 scripts/analyze_data_quality.py tests/fixtures/pass.json --pretty
```

The fixture returns separate `PASS` statuses and a receipt hash. A violation
fixture can fail `quality_status` while an unrelated monitoring gap separately
controls `monitoring_status`.

## Error Handling

- Analyzer exit `2`: input is malformed or unsafe; fix the normalized evidence.
- Collector permission error: report missing visibility and the least privilege
  needed; never escalate automatically.
- Enterprise feature unavailable: emit `DQ_EDITION_UNAVAILABLE` and an
  `INCONCLUSIVE` boundary.
- Conflicting or duplicate identifiers: reject the packet rather than guessing.

## Resources

- [Normalized evidence input contract](references/input-contract.md)
- [Primary-source notes](references/source-notes.md)
- [Snowflake data-quality monitoring documentation](https://docs.snowflake.com/en/user-guide/data-quality-intro)
