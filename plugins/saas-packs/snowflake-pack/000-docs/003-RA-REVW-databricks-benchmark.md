# Snowflake vs Databricks Pack Benchmark

**Status:** accepted comparative review
**Date:** 2026-08-30
**Beads:** `claude-zhc5.2`

## Finding

The Snowflake v1 pack has breadth without operational depth. It contains 30 skills,
but no scripts, hooks, agents, commands, or eval specifications. Its 20 weakest skills
are recognizable instances of a fixed tutorial taxonomy. The Databricks v2 pack has
five outcome-focused skills backed by 12 scripts, 21 references, nine commands, three
hooks, four agents, five eval specifications, and live control-plane integration.

| Measure | Snowflake v1 | Databricks v2 |
| --- | ---: | ---: |
| Live skills | 30 | 5 |
| Skill-tree files | 40 | 75 |
| References | 10 | 21 |
| Deterministic scripts | 0 | 12 |
| Commands | 0 | 9 |
| Hooks | 0 | 3 |
| Agents | 0 | 4 |
| Eval specifications | 0 | 5 |
| Research/design records, excluding license | 0 | 17 |

The problem is not word count. Snowflake v1 includes 170 inline code blocks, but none
are packaged as reusable, fixture-tested tools. Numeric marketplace grades measured
structural completeness; they did not prove that the skills solved distinct operator
jobs.

## Quality bar adopted from Databricks

A Snowflake skill earns a live slot only when it:

1. Has a distinct symptom, incident, or decision trigger.
2. Reads live or supplied evidence and says when evidence is unavailable or stale.
3. Moves deterministic classification and arithmetic into tested scripts.
4. Separates confirmed facts from estimates, hypotheses, and at-risk amounts.
5. Declares privileges, side effects, authority boundaries, and rollback.
6. Emits a measurable artifact an operator can review or hand off.
7. Loads detailed product knowledge from primary-source references on demand.
8. Carries positive, negative, edge, and adversarial evaluation cases.

Generic setup guides, SDK wrappers, architecture essays, static limit tables, and
checklists do not earn independent marketplace slots.

## Disposition of the 30 v1 skills

| v1 skill | Decision | v2 destination |
| --- | --- | --- |
| `snowflake-advanced-troubleshooting` | merge | `snowflake-query-forensics` |
| `snowflake-architecture-variants` | merge | deployment/access decision references |
| `snowflake-ci-integration` | replace | `snowflake-deploy-medic` |
| `snowflake-common-errors` | merge | `snowflake-query-forensics` |
| `snowflake-core-workflow-a` | replace | `snowflake-pipeline-guardian` |
| `snowflake-core-workflow-b` | replace | `snowflake-pipeline-guardian` |
| `snowflake-cost-tuning` | replace | `snowflake-cost-leak-hunter` |
| `snowflake-data-handling` | merge | `snowflake-access-guardian` |
| `snowflake-debug-bundle` | merge | `snowflake-query-forensics` |
| `snowflake-deploy-integration` | delete | deployment setup is not a skill |
| `snowflake-enterprise-rbac` | replace | `snowflake-access-guardian` |
| `snowflake-hello-world` | delete | setup moves to README/prerequisites |
| `snowflake-incident-runbook` | merge | `snowflake-query-forensics` and pipeline recovery |
| `snowflake-install-auth` | merge | README and skill prerequisites |
| `snowflake-known-pitfalls` | delete as slot | sourced cases move into references/evals |
| `snowflake-load-scale` | merge | query and cost workflows |
| `snowflake-local-dev-loop` | delete | generic scaffolding |
| `snowflake-migration-deep-dive` | merge | deployment medic; source-specific pilots require new evidence |
| `snowflake-multi-env-setup` | merge | deployment and access references |
| `snowflake-observability` | replace | pipeline/query/cost health outputs |
| `snowflake-performance-tuning` | replace | `snowflake-query-forensics` |
| `snowflake-policy-guardrails` | replace | `snowflake-access-guardian` |
| `snowflake-prod-checklist` | delete | checks move into skill evals/references |
| `snowflake-rate-limits` | delete | unsupported universal limits and unbounded retry |
| `snowflake-reference-architecture` | delete as slot | neutral decisions move into references |
| `snowflake-reliability-patterns` | merge | pipeline recovery; DR rehearsal remains a future candidate |
| `snowflake-sdk-patterns` | delete | generic wrapper documentation |
| `snowflake-security-basics` | merge | access and strong-auth workflows |
| `snowflake-upgrade-migration` | merge | `snowflake-deploy-medic` |
| `snowflake-webhooks-events` | merge | `snowflake-pipeline-guardian` |

## Release blockers found in v1

- Password-first examples conflict with the direction of Snowflake strong-auth policy.
- The Terraform examples use an obsolete provider namespace/version posture.
- The rate-limit skill presents account-independent numbers as universal facts and
  retries recursively without a bound.
- The policy guardrail skill constructs destructive dynamic SQL from arbitrary names
  and predicates.
- Observability examples use delayed Account Usage for near-real-time claims.
- Recovery examples use same-name `CREATE OR REPLACE ... CLONE` as rollback.
- Several skills present fixed warehouse sizes, quotas, multipliers, or RTO/RPO values
  without account evidence.

The safe remediation is a ground-up v2 rebuild and a documented migration map, not
incremental prose expansion of all 30 slots.
