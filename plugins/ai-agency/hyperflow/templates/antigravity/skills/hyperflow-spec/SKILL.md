---
name: hyperflow-spec
description: Hyperflow design phase. Use when the user is exploring an idea, weighing approaches, or has an ambiguous request — verbs like brainstorm, design, explore, "should we", "what's the best way to", "unsure about". Thinking, not building. Produces an approved design at .hyperflow/specs/<slug>.md, then hands off to hyperflow-scope.
---

# hyperflow-spec — design phase (Antigravity single-agent)

This phase is **thinking, not building**. No code until the design is approved. Follow the `hyperflow` doctrine (autonomy, file-first, AskUserQuestion gates).

## Steps

1. **Research first.** Read the relevant code, `AGENTS.md`, and `.hyperflow/memory/*` if present. Map the affected surface yourself. Do not ask what the code answers.
2. **Ask 2-5 clarifying questions** (floor: 2) via AskUserQuestion — only the *what/which/where* the code can't resolve. Multi-option questions mark one `(Recommended)`; binary ones don't.
3. **Propose 2-3 approaches** with one-line pros/cons/fit each. Recommend one; let the user pick.
4. **Design section-by-section.** Write the design to `.hyperflow/specs/<slug>.md` with this shape: status table → TL;DR (2-3 sentences) → Components → 1. Architecture → 2. Data flow → 3. Key decisions (with trade-offs accepted/rejected) → 4. Edge cases → 5. File structure (created/modified). Present it; ask `Approve all / Revise <section>`.
5. **On approval**, hand off: invoke the `hyperflow-scope` skill with the spec path.

## Rules

- Never write implementation code here.
- Never inflate a small task into a spec — economy matters. Trivial-clear requests skip straight to `hyperflow-scope`.
- The spec file is the artefact; chat shows only a short pointer to it.
