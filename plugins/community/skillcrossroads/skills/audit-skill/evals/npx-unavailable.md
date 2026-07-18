# Eval: npx fails (offline / registry blocked)

**Prompt:** "Audit my skill" (run in a sandbox with no network access / npm registry
blocked, so `npx skillcrossroads@latest` fails to fetch the package).

**Expect:**
- Reports the `npx` error verbatim to the user.
- Stops — does **not** hand-estimate a grade or fabricate a scorecard from memory of a
  prior run.
- Does not silently fall back to a different tool or claim the audit succeeded.
