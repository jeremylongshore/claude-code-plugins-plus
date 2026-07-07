# Content Consistency Validator

**Read-only discrepancy reports that catch messaging drift across your website, GitHub, and internal docs — every finding with a file, a line number, and a severity.**

## Problem

The website gets updated first and everything else lags: the README still shows last
release's version, internal training still quotes old pricing, and the same product is a
"plugin" on one surface and an "extension" on another. Catching that drift by hand means
manually diffing dozens of files across three surfaces after every change.

## Solution

One skill scans all three surfaces — any HTML-based website (static HTML, Hugo, Jekyll,
WordPress, Next.js, Vue, Gatsby, Docusaurus, and more), GitHub repository docs, and local
documentation — extracts versions, feature claims, contact info, and terminology, then
compares every source pair. Discrepancies land in a timestamped Markdown report,
severity-classified (Critical / Warning / Informational) and resolved against a declared
trust hierarchy: website > GitHub > local docs. It never modifies a file; the report is
the only artifact.

## W5

|           |                                                                                                                                                                         |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Content managers, documentation teams, technical writers, open-source maintainers — anyone keeping public and internal messaging aligned                                |
| **What**  | Scans website + GitHub + local docs, compares versions, feature claims, contact info, and terminology, and generates a severity-ranked read-only discrepancy report     |
| **When**  | Before updating internal docs or training materials; after website updates, releases, or rebrands; any time "does everything still say the same thing?" needs an answer |
| **Where** | Claude Code — auto-activating skill or explicit `/validate-consistency` command — run locally against the working repo; frontmatter also declares Codex and OpenClaw    |
| **Why**   | Hand-diffing three surfaces misses drift; this turns every mismatch into a file-and-line action item under a defined authority order, without touching a single file    |

## Stack

| Layer          | Choice                                                                               |
| -------------- | ------------------------------------------------------------------------------------ |
| Skill runtime  | Claude Code SKILL.md (single skill, no bundled scripts)                              |
| Command        | Legacy `/validate-consistency` slash command (`commands/`)                           |
| Comparison     | In-context analysis + shell text tools scoped to `Bash(diff:*)` and `Bash(grep:*)`   |
| Remote sources | WebFetch for deployed sites and GitHub raw content                                   |
| External APIs  | None                                                                                 |
| Output         | Timestamped Markdown report in `consistency-reports/`                                |
| Tool scope     | Read-only — no `Write`, no `Edit`, no git mutations anywhere in the declared surface |

## Differentiators

1. **Read-only by contract, not by convention.** The declared tool surface contains
   nothing that can mutate a file — the "it never changes anything" promise is
   structurally enforceable, so it's safe to point at production content on day one.
2. **A built-in authority order.** Website > GitHub > local docs is baked into the
   procedure, so every conflict comes back with a defined authoritative source and an
   update flow (website → GitHub → docs) instead of "these two files disagree."
3. **Findings are assignments, not investigations.** Every discrepancy ships with its
   file path, line number, severity class, and a concrete recommendation — the report
   reads as a prioritized fix list someone can be handed.
