# Snowflake v2 Portfolio Decision

**Decision:** accepted
**Date:** 2026-08-30
**Owner:** marketplace CTO
**Beads:** `claude-zhc5`

## Context

The Snowflake v1 pack claims 30 production-grade skills but largely ships tutorial
content. Research found six high-confidence operator jobs. The Databricks benchmark
showed that a smaller portfolio with deterministic tooling and evidence contracts is
more useful than a large template taxonomy.

## Decision

Snowflake v2 ships exactly six first-class skills:

1. **`snowflake-cost-leak-hunter`** — reconcile cost evidence, rank waste hypotheses,
   and emit a confidence-labeled FinOps report.
2. **`snowflake-query-forensics`** — diagnose a query, error, or workload regression
   using operator, queue, spill, pruning, blocking, and client evidence.
3. **`snowflake-pipeline-guardian`** — traverse task/dynamic-table/stream/Snowpipe
   dependencies to identify the first supported failure and ordered recovery.
4. **`snowflake-deploy-medic`** — assess Terraform, schemachange, CLI, driver, and
   behavior-change migrations without applying them.
5. **`snowflake-strong-auth-migration-pilot`** — inventory workload authentication
   dependencies and produce a staged WIF/PAT/OAuth/key-pair cutover packet.
6. **`snowflake-access-guardian`** — construct an effective role/grant graph, explain
   privilege paths, and produce a least-privilege dry-run diff.

Every skill must have deterministic fixture-tested analysis, substantial primary
references, an eval specification, explicit read-only and privilege boundaries, and
a named output artifact. A skill must label unavailable or delayed evidence and must
not turn hypotheses into claims.

## Compatibility and retirement

The plugin install slug remains `snowflake-pack`. The 30 v1 skill slugs are removed
from the installable portfolio and retained in Git history. The public marketplace
must provide permanent redirects from retired skill detail URLs to the closest v2
successor, and the README must carry a complete migration map. The deleting PR records
the exact restore commit and path pattern.

The v1 restore receipt is commit
`8302ef137e9ba717c4bdbe48b7f4c20ebe3a4169`. Restore the complete retired tree
without guessing with:

```bash
git restore --source=8302ef137e9ba717c4bdbe48b7f4c20ebe3a4169 -- \
  plugins/saas-packs/snowflake-pack/skills \
  skills/.curated/snowflake-debug-bundle \
  skills/.curated/snowflake-hello-world \
  skills/.curated/snowflake-prod-checklist
```

To inspect one artifact without restoring it, use
`git show 8302ef137e9ba717c4bdbe48b7f4c20ebe3a4169:<path>`.

This satisfies Blueprint 727 G9: content is recoverable from Git, the restore path is
named, and active internal references are migrated. The catalog is not inflated with
dead tombstone skills.

## Explicit non-goals

- No autonomous `ALTER`, `GRANT`, `REVOKE`, `APPLY`, resume, replay, resize, failover,
  or credential rotation.
- No embedded secrets, account-specific rates, universal thresholds, or invented
  SLAs.
- No new custom Snowflake MCP server in this slice. Skills may use read-only SQL/CLI,
  supplied extracts, or Snowflake-managed MCP where available and must degrade
  honestly when those surfaces are absent.
- No generic hello-world, SDK, checklist, architecture, or error-catalog skills.

## Deferred candidates

`snowflake-dr-rehearsal`, semi-structured schema-evolution analysis, and a narrowly
scoped SnowConvert verification pilot may be proposed only after separate demand and
capability research. They are not launch blockers and cannot be added to restore a
round skill count.
