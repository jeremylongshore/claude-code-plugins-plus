# The six rubric categories (skillcrossroads 0.11.4)

Every scan scores the artifact across six weighted categories. The overall letter grade is
the weighted average; each finding in the scorecard belongs to exactly one category and
cites file and line.

| Category | Weight | What it measures |
| --- | --- | --- |
| Triggering & Discoverability | 22% | Will Claude actually invoke this skill? Description quality, trigger cues, invocation-flag consistency (TRIGGER-01/02/03/05). |
| Correctness & Structure | 20% | Valid frontmatter, required fields, resolvable supporting-file references (STRUCT-01/02/05). |
| Clarity & Instructions | 18% | Unambiguous, contradiction-free instructions with stated constraints; no filler (CLARITY-02/03/05). |
| Token & Context Cost | 15% | Body length budget, progressive disclosure, description budget, recurring context cost (TOKEN-01/02/03/04). |
| Safety & Security | 15% | Hardcoded secrets, over-broad tool grants, auto-invoke risk, prompt-injection surface (SAFETY-01/02/03/04). |
| Verifiability & Maintainability | 10% | Eval coverage, maintenance hygiene, a checkable "done" definition (VERIFY-01/03/04). |

## Keyless vs. LLM-upgraded runs

- **Keyless (default):** all six categories score deterministically — no network calls
  beyond fetching the CLI, no API key, fully reproducible.
- **With `ANTHROPIC_API_KEY` set:** TRIGGER-01 upgrades Triggering to an LLM judge, and
  three LLM-assisted checks are added: VERIFY-04 (verification steps), CLARITY-02
  (contradictions), and CLARITY-05 (constraints). A failing LLM check is reported, never
  silently guessed.

The report always states which mode ran, so the reader knows what the grade covers.

## Reading a finding

Each finding carries a check ID (for example `SAFETY-02`), a status, the file:line evidence,
and a fix hint. **SAFETY-* findings are never suppressed or worked around** — fix the
underlying problem. Per-check fix documentation:
[skillcrossroads.com/docs/checks](https://skillcrossroads.com/docs/checks).
