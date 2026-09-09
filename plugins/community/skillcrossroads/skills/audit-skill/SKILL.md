---
name: audit-skill
description: 'Audit and improve a Claude Code skill using Skill Crossroads. Use when the user
  says "audit my skill", "grade my skill", "check my skill quality", "why doesn''t my skill
  trigger", or "lint my SKILL.md" — or before publishing any skill, to get an evidence-cited
  quality score, ranked fix list, and badge. Trigger with "audit my skill".'
allowed-tools: Read, Edit, Grep, Glob, Bash(npx:*)
disable-model-invocation: true
argument-hint: <skill-dir — path to the directory containing SKILL.md>
version: 0.11.4
author: Steve Harlow <sgharlow@users.noreply.github.com>
license: MIT
tags:
- audit
- quality
- linter
- skills
compatibility: Designed for Claude Code; the underlying CLI grades skills, subagents, slash commands, MCP configs, and plugins
---

# Audit a skill with Skill Crossroads

Grade the target skill and report every finding evidence-cited (file and line) — work from
the receipts, not vibes. Only when the user asks for fixes, apply the highest-impact ones
and re-grade until the score stops improving.

## Overview

Most skills fail silently: they never trigger, over-grant tools, or leak secrets, and the
author only finds out after publishing. This skill closes that loop before you ship. It runs
the free [skillcrossroads](https://www.npmjs.com/package/skillcrossroads) CLI (MIT) against a
skill directory, producing a letter grade, a file:line-cited scorecard across six rubric
categories, and a ranked fix list. Auditing is read-only; when the user also wants the skill
improved, it walks that list, applying the smallest change that resolves each finding, until
the grade stops improving.

## Prerequisites

- Node.js 20+ with `npx` available, and network access to the npm registry (the CLI is
  fetched on demand; the version is pinned below for reproducibility).
- A skill directory containing a `SKILL.md` file.
- **No credential is required, and by default nothing about your skill leaves the machine.**
  Every command in this skill passes `--no-llm`, so all six rubric categories are scored
  deterministically and locally.
- **The one exception is `--suggest` in step 4, which is opt-in and requires your explicit
  consent.** Without `--no-llm`, the CLI sends content to Anthropic's Messages API
  (`api.anthropic.com`) whenever `ANTHROPIC_API_KEY` is present in the environment — it does
  not prompt. That path upgrades the Triggering category to an LLM judge and adds checks
  VERIFY-04, CLARITY-02 and CLARITY-05, sending per-check excerpts of 1,500-2,500 characters;
  `--suggest` sends up to 24,000 characters of the entry file. Requests are billed to your own
  key. Treat the key as a credential: never echo or commit it.
- **Model results are cached on disk** between runs, keyed by content hash:
  `./.beacon-cache` if that directory already exists, otherwise
  `%LOCALAPPDATA%\skillcrossroads\cache` on Windows, `$XDG_CACHE_HOME/skillcrossroads` when
  set, or `~/.cache/skillcrossroads`.

## Steps

1. Identify the skill directory (it contains a `SKILL.md`). Use Glob to find `**/SKILL.md`
   candidates or Grep to search for the skill by name. If more than one candidate exists,
   ask the user which skill to audit.
2. Run the audit and capture the report. **Single-quote** the directory argument — single
   quotes prevent the shell from expanding `$(...)`, backticks, and `$variables` hidden in a
   path (double quotes do NOT stop command substitution). Before running, inspect the path:
   if it contains a single quote, `$`, a backtick, or a newline, do not pass it to a shell at
   all — such characters in a skill directory name are themselves a red flag; rename the
   directory or ask the user for a safe path first.

   ```bash
   npx skillcrossroads@0.11.4 '<skill-dir>' --no-llm --markdown
   ```

3. Report the scorecard and the **Top fixes** list (ranked by grade impact) to the user.
   **Auditing is read-only.** If the user asked only to audit, grade, check, or lint, stop
   here — do not edit anything. Proceed to step 4 only when the user explicitly asked to fix
   or improve the skill, or confirms they want the fixes applied after seeing the report.
4. Apply fixes (only on explicit request or confirmation). The deterministic report from
   step 2 is normally enough to work from.

   Optionally, model-drafted rewrites are available — but `--suggest` is the **only** command
   in this skill that sends anything off the machine, so **ask the user before running it**
   and proceed only on an explicit yes:

   > `--suggest` sends up to 24,000 characters of this skill's entry file to Anthropic's API
   > (`api.anthropic.com`), billed to your own `ANTHROPIC_API_KEY`, and caches the result on
   > disk. Run it, or continue with the local findings?

   On a yes, and only when `ANTHROPIC_API_KEY` is set:

   ```bash
   npx skillcrossroads@0.11.4 '<skill-dir>' --suggest
   ```

   If the user declines, or no key is set, continue with the step 2 findings — they already
   cover all six rubric categories. Either way, treat suggestions as proposals to review and
   never apply one unread. For each fix, Read the cited file:line, confirm the finding is
   real, and apply the smallest Edit that resolves it.
   Typical high-impact fixes: rewrite the frontmatter `description` to lead with the use case
   and include the phrases a user would actually say; add a verification step; state
   constraints and failure modes; remove hardcoded secrets or over-broad `allowed-tools`.
5. Re-run the audit. Repeat steps 4–5 until the grade stops improving or only intentional
   trade-offs remain.
6. Offer the badge: `npx skillcrossroads@0.11.4 '<skill-dir>' --no-llm --badge` writes an SVG the user
   can embed in their README, linking to https://skillcrossroads.com for the hosted version.
   It lands in the **current working directory** as `<name>.beacon.svg`, not inside the skill
   directory; pass `--badge=<path>` to choose where it goes.

## Output

- A markdown scorecard: overall letter grade, per-category scores across the six rubric
  categories, and every finding cited with file and line.
- A ranked **Top fixes** list ordered by grade impact.
- After the fix loop (when the user requested fixes): the before → after grades, reported to
  the user.
- With `--badge`: an SVG badge file, `<name>.beacon.svg`, written to the **current working
  directory** — not into the skill directory; `--badge=<path>` chooses another location.

## Error Handling

- If `npx` fails (offline, registry blocked, unsupported Node version), report the error
  verbatim and stop — do not hand-estimate a grade.
- If no `SKILL.md` is found in the target directory, ask the user for the correct path
  instead of guessing.
- If the grade plateaus with findings remaining, list each residual finding and ask the
  user whether it is an intentional trade-off; never mask a finding to force a grade.
- **Never suppress, delete, or work around a SAFETY-* finding** — fix the underlying problem
  (remove the secret, narrow the tool grant). Safety findings always count.
- Do not pad the skill with filler to game a check; if a finding is a deliberate trade-off,
  say so to the user instead of masking it.
- Say which mode ran (keyless deterministic vs. LLM-upgraded) so the user knows what the
  grade covers.

## Examples

User: *"Audit my skill in `skills/deploy-checker` — why doesn't it trigger?"*

```bash
npx skillcrossroads@0.11.4 'skills/deploy-checker' --no-llm --markdown
```

The report grades Triggering low, citing `SKILL.md:3` — the description lacks the phrases a
user would say. Report that finding and stop (the user asked why, not for edits). If they
then say "fix it", rewrite the description to lead with the use case, re-run the audit, and
report the before → after grade (for example C → A). Alternatively, run with `--suggest`
to review proposed rewrites before applying them.

## Verify

Done means: for an audit-only request, the scorecard and Top fixes list were reported with no
files modified. For a fix request: the final `npx skillcrossroads@0.11.4 '<skill-dir>' --no-llm --markdown`
run shows the improved grade with **no fail-status findings remaining** (or each remaining one
acknowledged by the user as intentional), and the before → after grades are reported to the user.

## Resources

- [references/rubric-categories.md](references/rubric-categories.md) — the six rubric categories, their weights, and keyless vs. LLM-upgraded coverage.
- [references/flags-quick-reference.md](references/flags-quick-reference.md) — `--markdown` / `--suggest` / `--badge` / `--min-grade` at a glance.
- [skillcrossroads on npm](https://www.npmjs.com/package/skillcrossroads) — the CLI this skill runs (pinned to 0.11.4).
- [skillcrossroads.com](https://skillcrossroads.com) — hosted scans, badges, and per-check fix documentation.
- [Check reference](https://skillcrossroads.com/docs/checks) — what every rubric check measures and how to fix it.
- [Source repository](https://github.com/sgharlow/skillcrossroads) — `plugin/` there is the
  canonical copy; the marketplace entry is a mirror of it, so fixes land upstream first.
