# Snowflake Skill Pack

> Eight model-neutral, evidence-driven operator skills for Snowflake cost,
> performance, pipelines, deployments, authentication, access governance, data
> quality, and failover readiness.

## Start in 30 seconds

Install the pack:

```bash
/plugin install snowflake-pack@claude-code-plugins-plus
```

That is the Claude Code install projection. The skill instructions and Python
analyzers do not call a model-specific API: Agent Skills-compatible harnesses can
load the skill directories directly, and any automation can invoke the bundled
analyzers from Python 3.10+ without an adapter.

Then describe the problem in plain language:

- “Why did our Snowflake bill jump?”
- “Find the root cause of query `01b...`.”
- “Why did this dynamic table stop refreshing?”
- “Is this Terraform upgrade safe?”
- “Move our service users off passwords.”
- “Why can this role read that table?”
- “Are our data-quality expectations actually covering the critical tables?”
- “Can this failover group meet our RPO and RTO?”

The matching skill asks for the smallest useful evidence set, analyzes it without
changing the account, and produces a reviewable report or change packet.

## The eight skills

| Skill | Use it when |
| --- | --- |
| `snowflake-cost-leak-hunter` | You need to explain spend, attribute credits, find idle or unowned cost, and rank savings hypotheses. |
| `snowflake-query-forensics` | A query is slow, queued, blocked, spilling, pruning poorly, failing, or has regressed. |
| `snowflake-pipeline-guardian` | Tasks, streams, dynamic tables, COPY, or Snowpipe are stale, suspended, delayed, rejecting data, or duplicating work. |
| `snowflake-deploy-medic` | Terraform, schemachange, CLI, driver, or behavior-change upgrades produce risky drift or migration failures. |
| `snowflake-strong-auth-migration-pilot` | Human or service workloads must move from legacy password access to WIF, PAT, OAuth, or key-pair authentication. |
| `snowflake-access-guardian` | You need an effective privilege trace, RBAC drift review, or least-privilege change packet. |
| `snowflake-data-quality-sentinel` | You need to distinguish violated expectations, failed evaluations, missing coverage, stale results, and monitoring gaps. |
| `snowflake-failover-readiness-drill` | You need a read-only RPO/RTO preflight or verification of an operator-executed failover/failback drill. |

## Collect live evidence without an adapter

Every workflow can analyze a supplied redacted JSON receipt. For an existing
least-privilege Snowflake CLI connection, the shared collector can also produce a
normalized, source-stamped receipt for any supported surface:

```bash
python3 shared/evidence/collect_snowflake_evidence.py \
  --surface query \
  --connection readonly-observer \
  --output ./snowflake-query-evidence.json
```

Supported surfaces are `cost`, `query`, `pipeline`, `access`, `auth`,
`data-quality`, and `replication`. The collector statically rejects mutating SQL,
does not accept credentials, records view/timestamp/hash provenance, and treats
permission gaps as missing evidence rather than permission to escalate.
If a receipt sets `truncation_possible: true`, narrow or partition the requested
window before making any completeness, absence, or pass claim.

## Safety model

The pack is evidence-first and recommendation-only by default.

- No skill automatically runs `ALTER`, `GRANT`, `REVOKE`, Terraform `apply`, pipeline
  resume/replay, warehouse resize, failover, or credential rotation.
- Account Usage and Organization Usage latency is reported, not hidden.
- Confirmed facts, estimates, hypotheses, and at-risk amounts are labeled separately.
- Customer pricing, editions, privileges, policies, and SLAs are never guessed.
- Generated SQL and change plans are dry-run artifacts until an authorized operator
  reviews and executes them through normal change control.

Each skill can work from the bundled read-only collector, evidence returned by a
separately configured MCP connector, or supplied/redacted extracts. This pack does
not ship an MCP server or own authentication. Missing evidence reduces confidence;
it never becomes a fabricated “pass.”

## Authentication

Use an existing Snowflake connection with the least privilege needed for the selected
evidence views. Prefer workload identity federation, programmatic access tokens,
OAuth, or key-pair authentication according to your account policy and client support.
Do not paste secrets into a prompt, report, fixture, or repository.

Each skill lists its exact evidence and privilege requirements. A missing view or
grant produces a blocked-evidence finding and a narrowly scoped request—not a demand
for `ACCOUNTADMIN`.

## Migration: v1 → v2.1

Version 2 replaced 30 documentation-style skills with six operator workflows;
version 2.1 adds the two research-justified gaps plus shared live collection. The
plugin install slug remains `snowflake-pack`. Retired public skill URLs permanently
redirect to the closest successor, and Git history retains every v1 artifact.

Restore receipt: v1 is preserved at
`8302ef137e9ba717c4bdbe48b7f4c20ebe3a4169`; the exact restore command is in
[`000-docs/004-AT-ADEC-v2-portfolio-decision.md`](000-docs/004-AT-ADEC-v2-portfolio-decision.md).

| v1 skill | v2 destination |
| --- | --- |
| `snowflake-cost-tuning` | `snowflake-cost-leak-hunter` |
| `snowflake-advanced-troubleshooting` · `snowflake-common-errors` · `snowflake-debug-bundle` · `snowflake-incident-runbook` · `snowflake-known-pitfalls` · `snowflake-load-scale` · `snowflake-performance-tuning` · `snowflake-rate-limits` | `snowflake-query-forensics` |
| `snowflake-core-workflow-a` · `snowflake-core-workflow-b` · `snowflake-observability` · `snowflake-reliability-patterns` · `snowflake-webhooks-events` | `snowflake-pipeline-guardian` |
| `snowflake-architecture-variants` · `snowflake-ci-integration` · `snowflake-deploy-integration` · `snowflake-local-dev-loop` · `snowflake-migration-deep-dive` · `snowflake-multi-env-setup` · `snowflake-prod-checklist` · `snowflake-reference-architecture` · `snowflake-sdk-patterns` · `snowflake-upgrade-migration` | `snowflake-deploy-medic` |
| `snowflake-install-auth` · `snowflake-hello-world` | `snowflake-strong-auth-migration-pilot` plus this README’s setup guidance |
| `snowflake-data-handling` · `snowflake-enterprise-rbac` · `snowflake-policy-guardrails` · `snowflake-security-basics` | `snowflake-access-guardian` |

This is a deliberate consolidation. Generic tutorials, fixed sizing tables, universal
rate limits, password-first examples, and copy/paste destructive recipes were removed
rather than preserved to inflate the catalog.

## Design records

The evidence, comparative audit, and portfolio decision are indexed in
[`000-docs/000-INDEX.md`](000-docs/000-INDEX.md).

## License

MIT
