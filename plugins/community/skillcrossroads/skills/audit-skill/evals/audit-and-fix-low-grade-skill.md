# Eval: audit and fix a skill with real findings

**Prompt:** "Why doesn't my skill trigger? It's at ./flaky-skill."

**Setup:** `./flaky-skill` has a thin description with no "Use when..." cues (a real
TRIGGER-02/03 finding) and no `evals/` folder (a real VERIFY-01 finding).

**Expect:**
- Runs the audit and reads the ranked **Top fixes** list rather than guessing.
- For the triggering finding, opens the cited `SKILL.md:line`, confirms it's real, and
  rewrites the description to lead with the use case and include phrases a user would
  actually say — the smallest change that resolves it, not a full rewrite.
- Does not touch any SAFETY-* finding by suppressing or deleting it.
- Re-runs the audit after applying fixes and reports the before → after grade.
