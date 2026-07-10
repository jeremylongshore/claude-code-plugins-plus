---
name: validate-consistency
description: Run the document consistency audit via the validate-consistency skill
category: documentation
---

# /validate-consistency

Run the full document consistency audit. This command is a thin invoker — the entire protocol lives in the `validate-consistency` skill.

## Steps

1. Invoke the `validate-consistency` skill on the current working directory. Pass through any scope or registry path the user supplied (e.g. an alternate `sot-map.yaml` location).
2. The skill loads the per-fact-class authority registry (default `~/000-projects/intent-os/sot-map.yaml`), inventories documentation artifacts, and runs all applicable drift checks — deterministic and LLM-judged lanes structurally separated.
3. Present the skill's report as produced: deterministic findings (Part A), advisory LLM-judged findings (Part B), unowned fact-class callouts, proposed registry rows (bootstrap drafts), and priority actions.

Read-only: the audit reports discrepancies and never modifies files.

Invoked automatically by `/release` during Phase 1.6 — deterministic Critical findings feed the release blocking gate; advisory findings never block.
