# PRD: skillcrossroads

**Author:** Steve Harlow
**Date:** 2026-07-23
**Status:** Active

## Problem

Skill authors ship SKILL.md files that never trigger, over-grant tools, or leak secrets —
and only find out after publishing, when users report the skill "does nothing" or a review
flags a safety issue. There is no in-editor feedback loop: the author's only options today
are manual review against scattered best-practice docs, or publishing and waiting. The
skillcrossroads CLI exists (npm, MIT) but requires leaving Claude Code to run and interpret
it by hand.

## Target users

| User                 | Context                                                | Primary need                                              |
| -------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| Skill author         | Writing or revising a SKILL.md before publishing        | An evidence-cited grade and ranked fix list, in one step   |
| Plugin maintainer    | Reviewing contributed skills in a marketplace repo      | A repeatable, deterministic quality bar with file:line receipts |
| Claude Code power user | A personal skill stopped triggering after edits       | Diagnosis of why the description no longer matches intent  |

## Success criteria

1. `npx skillcrossroads@0.11.3 <skill-dir> --markdown` runs from inside Claude Code and
   returns a letter grade plus findings, each cited with file and line — no hand-estimated
   grades, ever (the skill stops and reports the error verbatim if the CLI fails).
2. The audit-fix-re-audit loop measurably raises the grade (before → after reported to the
   user) or terminates with each residual finding explicitly acknowledged as an intentional
   trade-off.
3. Runs are deterministic and local by default: every command passes `--no-llm`, scoring all
   six rubric categories without contacting any model, whether or not `ANTHROPIC_API_KEY` is
   set. The LLM-judge upgrade is reachable only through the consented `--suggest` path in
   SKILL.md step 4, and the mode that ran is reported either way.

## Functional requirements

- **FR-1:** Grade a skill directory via the pinned CLI (`npx skillcrossroads@0.11.3`) and
  present the scorecard and ranked Top fixes list.
- **FR-2:** Apply the smallest edit that resolves each confirmed finding, re-run the audit,
  and iterate until the grade stops improving.
- **FR-3:** Never suppress or mask a SAFETY-* finding — fix the underlying problem or
  surface it to the user.
- **FR-4:** Offer an embeddable SVG badge (`--badge`) once the final grade is reported.

## Package naming

The upstream CLI is the un-scoped `skillcrossroads` npm package, maintained at
[github.com/sgharlow/skillcrossroads](https://github.com/sgharlow/skillcrossroads). The
`package.json` in this plugin directory is the marketplace's generated tracking/proof
artifact and follows the repo-wide convention of publishing catalog plugins under the
`@intentsolutionsio` npm scope; it is not the CLI and not an ownership claim over it.

## Out of scope

- Grading artifacts other than by delegating to the CLI (no hand-rolled rubric in the skill).
- Auto-publishing or badge hosting.
- Any network call the user has not agreed to. Two are possible, and both are named here
  rather than implied: fetching the pinned CLI from the npm registry (every run), and the
  opt-in `--suggest` in SKILL.md step 4, which sends up to 24,000 characters of the target
  skill's entry file to Anthropic's Messages API under the user's own `ANTHROPIC_API_KEY`
  after explicit consent. Every other command this skill issues passes `--no-llm` and is
  fully local.

  > Corrected 2026-09-03. This bullet previously read "any network call beyond fetching the
  > pinned CLI from the npm registry", which was not true of the CLI's behaviour: without
  > `--no-llm` it contacts Anthropic whenever `ANTHROPIC_API_KEY` is set in the environment,
  > without prompting. The skill now passes `--no-llm` everywhere except the consented
  > `--suggest` path, so the boundary this document describes is the one the commands
  > actually enforce.
- Editing skills without the user's awareness — every fix is applied from a cited finding
  the user can inspect.
