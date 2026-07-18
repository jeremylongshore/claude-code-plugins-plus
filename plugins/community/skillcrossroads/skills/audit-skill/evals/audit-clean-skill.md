# Eval: audit a skill that already scores well

**Prompt:** "Audit my skill at ./my-skill — grade my skill quality."

**Setup:** `./my-skill` is a small, well-formed skill (valid frontmatter, a clear
description with "Use when..." trigger cues, an evals/ folder, no secrets).

**Expect:**
- Runs `npx skillcrossroads@latest ./my-skill --markdown` (does not hand-estimate a grade).
- Reports the actual overall score/grade and states whether the LLM-assisted checks ran
  (i.e. whether `ANTHROPIC_API_KEY` was set).
- Since there are no fail-status findings, does NOT invent fixes to apply — reports the
  skill as done, optionally naming any remaining warn-status findings as intentional
  trade-offs if the user says so.
