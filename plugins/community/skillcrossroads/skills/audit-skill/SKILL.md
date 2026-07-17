---
name: audit-skill
description: 'Audit and improve a Claude Code skill using Skill Crossroads. Use when the user
  says "audit my skill", "grade my skill", "check my skill quality", "why doesn''t my skill
  trigger", or "lint my SKILL.md" — or before publishing any skill, to get an evidence-cited
  quality score, ranked fix list, and badge.'
allowed-tools: Read, Edit, Grep, Glob, Bash(npx:*)
version: 0.11.3
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

Grade the target skill, apply the highest-impact fixes, and re-grade until the score stops
improving. Every finding is evidence-cited (file and line) — work from the receipts, not vibes.

## Steps

1. Identify the skill directory (it contains a `SKILL.md`). If more than one candidate exists,
   ask the user which skill to audit.
2. Run the audit and capture the report:

   ```bash
   npx skillcrossroads@latest <skill-dir> --markdown
   ```

3. Read the **Top fixes** list (ranked by grade impact). Optionally, if `ANTHROPIC_API_KEY`
   is set, run `npx skillcrossroads@latest <skill-dir> --suggest` to get proposed
   current → proposed fixes for the top findings — treat them as proposals to review, never
   apply one unread. For each fix, open the cited
   file:line, confirm the finding is real, and apply the smallest change that resolves it.
   Typical high-impact fixes: rewrite the frontmatter `description` to lead with the use case
   and include the phrases a user would actually say; add a verification step; state
   constraints and failure modes; remove hardcoded secrets or over-broad `allowed-tools`.
4. Re-run the audit. Repeat steps 3–4 until the grade stops improving or only intentional
   trade-offs remain.
5. Offer the badge: `npx skillcrossroads@latest <skill-dir> --badge` writes an SVG the user
   can embed in their README, linking to https://skillcrossroads.com for the hosted version.

## Constraints

- **Never suppress, delete, or work around a SAFETY-* finding** — fix the underlying problem
  (remove the secret, narrow the tool grant). Safety findings always count.
- Do not pad the skill with filler to game a check; if a finding is a deliberate trade-off,
  say so to the user instead of masking it.
- If `npx` fails (offline, registry blocked), report the error verbatim and stop — do not
  hand-estimate a grade.
- LLM-assisted checks only run when `ANTHROPIC_API_KEY` is set. Keyless skill grades are
  still full — all six rubric categories score deterministically (rubric v1.1+); a key
  upgrades Triggering to the LLM judge and adds VERIFY-04, CLARITY-02, and CLARITY-05.
  Say which mode ran.

## Verify

Done means: the final `npx skillcrossroads@latest <skill-dir> --markdown` run shows the improved
grade with **no fail-status findings remaining** (or each remaining one acknowledged by the user
as intentional), and the before → after grades are reported to the user.
