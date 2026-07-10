# Web-research-first protocol

The shared online-research step every specialist agent (see [`../../agents/README.md`](../../agents/README.md))
invokes before it judges or investigates. Training data is stale; framework APIs, CVEs, and best practices move
faster than any model's cutoff. A specialist that asserts a current best practice without checking is guessing.

This file is the **single source of truth**. Specialist charters reference it by one line —
`Web-research-first: per web-research.md, scope=<…>` — and never restate it.

## Mandate

When a specialist runs on a **gated flow** (see below), it performs a focused online pass **before** producing its
verdict or findings, then cites what it used. The research informs the judgement; it does not replace the bound
persona's standards.

## Flow gating (when it runs)

Web-research-first fires **only** when the active flow profile is one of:

| Condition | Runs? |
|---|---|
| `flow ∈ { deep, research, scientific }` | yes |
| triage `security: true` (any flow) | yes |
| `audit` / `deploy` invocation | yes (these are gated-in by definition) |
| `flow ∈ { fast, standard, creative }` AND not `security` | **no — skipped** |

On a non-gated flow the specialist proceeds on persona standards + project memory alone. This keeps the common path
as cheap and fast as today; the online cost is only paid where currency materially changes the verdict.

## Skip conditions (even on a gated flow)

Skip — and **log the skip on one line**, never silently — when ANY holds:

- **Offline / `WebSearch` unavailable** → `web-research: skipped (offline)`.
- **Cached-fresh** — a finding for this surface exists in `.hyperflow/memory/` tagged `#research #specialist`, dated
  within the recency window → `web-research: skipped (cache hit: <entry>)`.
- **Config off** — `specialists.webResearch.enabled: false` → `web-research: skipped (disabled)`.

A skip is graceful degradation, never a failure — it must not block the chain (same posture as triage fallback).

## Tools

| Tool | Use for |
|---|---|
| `WebSearch` | discovery — find current advisories, release notes, best-practice sources |
| `WebFetch` | read a specific source identified by search or already known (changelog, CVE entry, doc page) |
| `context7` MCP (when available) | authoritative, version-pinned library/framework docs (matches the `research` persona convention) |

## Source budget

- Default **3–5** sources (`specialists.webResearch.maxSources`, default 5).
- `security-reviewer` / `vulnerability-reviewer` / `compliance-reviewer`: **floor of 5**.
- Stop early once the question is answered with corroboration — do not pad to the cap.

## Recency bias

- Prefer sources within `specialists.webResearch.recencyMonths` (default **18 months**).
- CVE / security advisories: prefer the **last 6 months**, but always include the originating advisory regardless of age.
- Always confirm the **current major version** of any framework/library named in the diff — a best practice for v4
  may be an anti-pattern in v6.

## Citation format (mandatory)

Every research-informed finding cites its source inline: `<title> — <URL> (<YYYY-MM>)`.

The specialist's output ends with a `Sources consulted:` block listing each source used. **An uncited
best-practice or CVE claim is a doctrine violation** — it is indistinguishable from a hallucinated one (mirrors the
`research` persona's evidence rule).

```
Sources consulted:
- React 19 `useActionState` migration — https://react.dev/blog/… (2025-12)
- CVE-2025-XXXXX advisory — https://github.com/advisories/… (2026-03)
```

## Token discipline

Research output is a **short cited brief**, not raw page dumps. Fetch, extract the load-bearing fact, cite, discard
the rest. The brief feeds the verdict; the pages do not enter the chain transcript. (Honours the output-discipline
rule — research adds signal, not bulk.)

## Caching — closing the cost loop

Durable findings (a confirmed best practice, a CVE applicability decision, a version-specific gotcha) append to
`.hyperflow/memory/learnings.md` (or `pitfalls.md` for an avoided trap) tagged `#research #specialist <surface>`.
The next run on the same surface hits the **cached-fresh** skip above — the gated-flow online cost is paid once per
surface, not every run. Use the [`cache`](../cache/SKILL.md) memory format.

## Failure recovery

`WebSearch` / `WebFetch` errors follow [`failure-recovery.md`](failure-recovery.md): retry once, then degrade to the
skip path with a logged reason. Never abort the chain over a research failure.
