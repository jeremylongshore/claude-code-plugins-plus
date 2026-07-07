# ADR: 000-jeremy-content-consistency-validator — single-pass read-only skill with a report-only contract

> Filed at `docs/ADR.md` beside the rest of the submission set, per
> `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills"). The ADR template's `000-docs/` filing note is the known
> alternative reading; the first-party `docs/` convention follows the databricks-pack
> backfill precedent (PR #989).

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-07
**Status:** Accepted — current implementation, **superseded-in-planning** by the #991
multi-agent rebuild (Fable's recommendation); the rebuild files its own ADR.

## Context

The product contract ([`docs/PRD.md`](PRD.md)) is a cross-surface consistency audit whose
one non-negotiable is trust: the user must be able to run it against their live website,
public GitHub repos, and internal docs with zero risk that anything gets modified. The
comparison itself is not purely mechanical — the README commits to exact, fuzzy
(90%+ similarity), semantic, and pattern-based matching — so some judgment lives in-model
rather than in scripts. And the output has to be actionable by a non-participant: every
finding needs a file path, a line number, a severity, and a recommendation grounded in a
declared authority order (website > GitHub > local docs). Doing nothing means users
hand-diff dozens of files across three surfaces after every website change.

## Decision

Ship the validator as a **single-pass, read-only Claude Code skill** — one SKILL.md with
an eight-step procedure (discover → extract → verify → compare → classify → prioritize →
report → save) — plus a **legacy `commands/validate-consistency.md` slash command** for
explicit invocation. No agents, no bundled scripts: source discovery and extraction run
through narrowly-scoped shell text tools (`Bash(diff:*)`, `Bash(grep:*)`), remote
surfaces are fetched with WebFetch, and the fuzzy/semantic comparison happens in-context.
The trust hierarchy (website > GitHub > local docs) is hard-coded into the procedure, and
the only artifact a run produces is a timestamped Markdown report under
`consistency-reports/`.

## Alternatives considered

| Alternative                                                                | Why rejected                                                                                                                                                                                           |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Multi-agent pipeline (discovery / extraction / comparison / report agents) | More machinery than the v1 contract needed; a single-pass skill ships with zero orchestration surface. This rejection is now reversed in planning — the #991 rebuild adopts exactly this architecture. |
| Deterministic script-based comparator (bundled `scripts/`)                 | Pure scripts handle exact and regex matching but not the fuzzy/semantic matching the product claims; staying scriptless also keeps install zero-dependency across hosts.                               |
| Write-enabled auto-fixer                                                   | Breaks the core trust contract. "You maintain complete control — the plugin only reports, you decide what to fix" is the product's first promise, not an implementation detail.                        |
| Command-only plugin (no skill)                                             | Loses natural-language auto-activation ("check consistency before I update training materials"). The command was kept alongside the skill instead — see the legacy-format consequence below.           |

## Consequences

**Positive:**

- Zero write risk by construction: no `Write`, no `Edit`, no git mutation anywhere in the
  declared tool surface — the read-only guarantee is enforceable, not aspirational.
- Zero-dependency install: no scripts, no runtime, nothing to build; the skill works
  wherever SKILL.md works (frontmatter declares Claude Code, Codex, OpenClaw).
- Two invocation paths: natural-language skill activation plus an explicit
  `/validate-consistency` command.
- Deterministic report location and structure — timestamped file, fixed sections — so
  successive runs are comparable.

**Negative / accepted tradeoffs:**

- **Tool-scope debt** (validation baseline, 2026-07-07): `allowed-tools` declares
  `Grep`, `Read`, and `WebSearch`, but the SKILL.md body never references them —
  over-permissive/stale scope, flagged as 3 of the 6 marketplace-tier warnings. To be
  corrected in the #991 rebuild.
- Single-pass, in-context comparison caps depth: no project-type auto-detection, no
  deterministic drift checks — the gap that motivated the #991 multi-agent rebuild.
- The legacy command duplicates the skill's job in the older `commands/` format; it
  passes standard tier, but Anthropic guidance says new plugins use `skills/`. Two
  surfaces for one behavior invite drift between them.
- **Shadowing defect** (epic #991): skill precedence resolves `/validate-consistency` to
  the global `~/.claude` skill of the same name, so this plugin is shadowed in its own
  author's environment and has drifted into a thin shell (682-word SKILL.md) relative to
  the global engine. The single-pass architecture made that thinning easy to miss.

## Tool-permission scope

The frontmatter declares six entries and nothing mutating — no bare `Bash`, no `Write`,
no `Edit`. Entries marked ✱ are declared but never referenced in the SKILL.md body
(validation baseline 2026-07-07, warnings 1–3); they are retained here as recorded debt,
not as justified scope, pending the #991 rebuild.

| Tool           | Why it's needed                                                                                     |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `Read` ✱       | Intended for loading local docs and build output as comparison sources; body never invokes it.      |
| `WebFetch`     | Fetch deployed website pages and GitHub raw content when the surface is remote (per Prerequisites). |
| `WebSearch` ✱  | No use documented in the body; stale grant to be removed or justified in the rebuild.               |
| `Grep` ✱       | Intended for structured-data extraction across sources; the body uses `Bash(grep:*)` instead.       |
| `Bash(diff:*)` | Pairwise comparison of extracted fields between sources (step 4 of the procedure).                  |
| `Bash(grep:*)` | Source discovery and extraction of versions, feature claims, and contact info (steps 1–2).          |
