# Specialist Agent Registry

Named, domain-specialized agents that the Hyperflow chain dispatches. Each is a real Claude Code sub-agent
(`agents/<name>.md`, auto-discovered by the plugin) with frontmatter (`name`, `description`, `tools`) and a
charter body. Every specialist runs on the current session model — there is no `model:` field.

This registry is a **new system that reuses and extends** the 15 personas in
[`../skills/hyperflow/personas-A.md`](../skills/hyperflow/personas-A.md) /
[`personas-B.md`](../skills/hyperflow/personas-B.md). Personas are *standards text*. Specialists are *named agents*
that **bind** persona standards and add what personas lack.

## The DRY guard (non-negotiable)

A specialist **binds** persona(s) for its domain standards and adds only these specialist-only fields:

1. **Mission** — the one thing this agent catches or produces.
2. **Web-research-first** — a one-line pointer to [`../skills/hyperflow/web-research.md`](../skills/hyperflow/web-research.md) + its source-priority scope.
3. **Sub-agent fan-out authority** — whether it may spawn sub-workers, and the limits.
4. **Strict checklist / output contract** — its PASS bar, referencing the bound persona's "Things to verify"
   rather than copying it, plus specialist-only items.

**A charter that restates its persona's objectives / conventions / anti-patterns verbatim is a doctrine
violation.** Bind by reference — exactly how `personas-B.md` references `personas-A.md`.

> **Agent vs. persona naming.** `architect` is the one agent that shares a persona's exact name: the `architect`
> *agent* (a named specialist, hybrid design decision agent + reviewer) **binds** the `architect` *persona*
> (standards text in `personas-A.md`). Agent = who is dispatched; persona = the standards it applies.

## How specialists are selected — the Brain

Selection is **not** free-chosen by each skill. The flow is:

1. **Triage** (Haiku) emits a candidate `specialists[]` from `types[]` via the fixed derivation table in
   [`../skills/hyperflow/task-triage.md`](../skills/hyperflow/task-triage.md).
2. **[Brain](brain.md)** (decision-maker) is consulted **once** after triage. It finalizes the
   responsible roster, decides per-specialist web-research (legal only on gated flows), and approves any fan-out.
   On `fast`/`standard` flows Brain is a thin auto-approve of the triage table (no separate dispatch); on
   `deep`/`research`/`scientific`/`security` it actively reasons.
3. The Brain's decision is written into the artefact (spec status block → scope task file) and **inherited
   downstream** — no skill re-derives the roster.

`amplify` / `spec` / `scope` **announce** the responsible specialists. `dispatch` / `audit` / `trace` / `deploy`
**dispatch** the named specialist as the reviewer/investigator at its tier.

## Roles — one model, different responsibilities

Every specialist runs on the **current session model** — there is no model-tier routing and no per-provider catalog.
The same charter runs on Claude Code, Codex, OpenCode, Antigravity, or any host, because it inherits whatever model
the session uses. Specialists differ by **role**, not model:

- **Reviewer specialists** act as the per-batch Reviewer in-flight and as a standalone / final-integration Reviewer
  outside a batch (`--thorough` adds a standalone / final-integration review pass). Security/correctness specialists
  (`security-reviewer`, `vulnerability-reviewer`, `data-ml-reviewer`, `compliance-reviewer`) always run a **full
  review pass even per-batch** ("if security present, never fast").
- **Investigators** — `searcher` is a Worker; `debugger` / `analyst` / `researcher` are decision agents.
- **Brain** is a decision-maker / router, with a free cheap-path on `fast`/`standard` flows.

## Roster

### Reviewers
| Agent | Binds personas | Role | Focus |
|---|---|---|---|
| [frontend-reviewer](frontend-reviewer.md) | frontend, ui | reviewer | render, state, component correctness |
| [backend-reviewer](backend-reviewer.md) | api, architect | reviewer | service layer + module boundaries |
| [api-reviewer](api-reviewer.md) | api | reviewer | contract, status codes, validation |
| [database-reviewer](database-reviewer.md) | db | reviewer | migration correctness, reversibility, schema safety |
| [database-optimization-reviewer](database-optimization-reviewer.md) | db, performance | reviewer (full pass) | query optimization, indexing strategy, plan-level "better solution?" |
| [security-reviewer](security-reviewer.md) | security | reviewer (full pass) | authz, secrets, OWASP; halts on violation |
| [vulnerability-reviewer](vulnerability-reviewer.md) | security, scientific | reviewer (full pass) | CVE / dependency / exploit-path |
| [devops-reviewer](devops-reviewer.md) | devops | reviewer | CI, IaC, rollback, observability |
| [performance-reviewer](performance-reviewer.md) | performance | reviewer | profiling, caching, regression budgets |
| [algorithm-reviewer](algorithm-reviewer.md) | performance, scientific | reviewer | Big-O complexity + data-structure choice; proposes lower-complexity algorithms |
| [accessibility-reviewer](accessibility-reviewer.md) | ui, frontend | reviewer | WCAG, keyboard, screen-reader |
| [mobile](mobile.md) | frontend, ui, performance | reviewer + design decision agent | framework choice, app architecture, platform a11y, device-size testing, on-device perf |
| [data-ml-reviewer](data-ml-reviewer.md) | scientific, db | reviewer (full pass) | reproducibility, numerical correctness, lineage |
| [compliance-reviewer](compliance-reviewer.md) | security, docs | reviewer (full pass) | PII / GDPR / audit-trail / regulatory |
| [architect](architect.md) | architect | reviewer + design decision agent | system decomposition, boundaries, failure modes, ADRs, frontend-at-scale |
| [designer](designer.md) | ui, creative | reviewer + design decision agent | design system, visual/experiential design, prior-art research, anti-slop |
| [motion](motion.md) | ui, performance | reviewer + motion decision agent | animation, 60fps compositor budget, physics/springs, reduced-motion |

The **(full pass)** reviewers always run a complete review even per-batch ("if security present, never fast"); the others run an anchored per-batch review in-flight and a full standalone review outside a batch.

### Investigators
| Agent | Binds personas | Role | Focus |
|---|---|---|---|
| [searcher](searcher.md) | research | worker | codebase + docs surface mapping |
| [debugger](debugger.md) | bugfix, test | decision agent | root-cause, 5-Whys, hypothesis testing |
| [analyst](analyst.md) | architect, research | decision agent | multi-dimensional analysis / decision synthesis |
| [researcher](researcher.md) | research | decision agent | external evaluation, library survey, deep web research |

### Router
| Agent | Role | Focus |
|---|---|---|
| [brain](brain.md) | decision-maker / router | selects the responsible specialist roster; decides web-research + fan-out |

## Sub-agent fan-out

Only agents whose charter sets fan-out `allowed` (investigators + standalone/final reviewers) may spawn sub-workers,
**depth-capped at 1**, budget ≤ 3 (≤ 5 for `vulnerability-reviewer` / `researcher`). Full rules:
[`../skills/hyperflow/DOCTRINE.md`](../skills/hyperflow/DOCTRINE.md) Layer 3 — sub-agent fan-out.

## Agent consultation (every agent, automatic)

**Every agent here — current and future — can ask another for help mid-task, with no opt-in.** A build worker emits
`CONSULT: <peer> — <question>` and the orchestrator brokers it; a design-time decision agent consults a peer
directly. The capability lives in the shared prompt scaffolding ([`../skills/hyperflow/worker-prompt.md`](../skills/hyperflow/worker-prompt.md) /
[`reviewer-prompt.md`](../skills/hyperflow/reviewer-prompt.md)), not in any charter — so a new `agents/<name>.md`
participates the moment it exists. The **allowlist is this directory** (resolved by file existence); a charter's
`Composes with:` line is only the *recommended-peer hint*. Depth-1, budget ≤ 2 (worker) / ≤ 3 (decision agent),
never overrides a security halt. Full contract: [`../skills/hyperflow/consultation.md`](../skills/hyperflow/consultation.md)
· [`DOCTRINE.md`](../skills/hyperflow/DOCTRINE.md) rule 19.

## Agent-file template

> Consultation needs no field — every agent gets it free via the shared prompt scaffolding. `Composes with:` just
> ranks the peers this agent is most likely to consult.

```
---
name: <name>
description: Use when <triggering surface/condition>.
tools: Read, Grep, Glob, Agent, WebSearch, WebFetch
---
**Family / Binds personas / Default role / Triggered by types:** …
**Mission:** …
**Web-research-first:** per ../skills/hyperflow/web-research.md. Scope: …
**Sub-agent fan-out:** allowed|not — limits.
**Strict checklist / output contract:** …
**Output format:** verdict block | findings block; `Sources consulted:` when research ran.
**Composes with:** …
```
