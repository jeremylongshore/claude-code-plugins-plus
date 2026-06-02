# Worker Prompt Template (Lean)

Lean variant of `worker-prompt.md`. Use this as the default template for parallel sibling sub-tasks dispatched by `dispatch`. Use the full `worker-prompt.md` only when `depth=max` or `--thorough` is requested.

**Why lean:** smaller prompts = faster time-to-first-token (TTFT) at the API layer = lower wall-clock latency per worker call. Workers still access the full project context — they fetch it on demand via `Read` instead of receiving it inlined.

## Template

```
## Task
[One clear objective — what to do, not how to think about it]

## Files in scope
[Exact file paths the worker should read/modify]

## Context
[What this file/module does, relevant conventions or constraints specific to this task]

## Memory references (read on demand)
Read these files only if needed. Locations differ — check both groups:

**Preferred single-read entry point:**
  - `.hyperflow/memory/session-context.md` — bundled profile + architecture + conventions, populated by the `session-start` hook at the start of each Claude Code session. Read this ONE file instead of the three sources below to save file reads per worker.

**Fallback (when session-context.md is absent or stale):** Read the source files individually from `.hyperflow/` root (written by scaffold Step 1):
  - profile.md        — project conventions
  - architecture.md   — system architecture
  - conventions.md    — naming, patterns, standards

`.hyperflow/memory/` (written by scaffold Step 2 / dispatch wrap-up):
  - doctrine.md       — orchestration rules
  - learnings.md      — accumulated lessons from prior batches
  - decisions.md      — recorded architectural decisions
  - pitfalls.md       — known failure modes
  - patterns.md       — reusable solution patterns

Read a file once if the task touches its domain. Do not re-read files already in your context window.

## Constraints
- Only modify files listed in scope
- Follow project coding standards (CLAUDE.md)
- Do not add "Co-Authored-By: Claude" to any git operation
- Token economy: be specific and to the point. No preamble, no postamble, no brief-restating, no narration. Return exactly the Output format below and stop (per DOCTRINE rule 16)

## Security Constraints
- Do NOT read/modify: .env, *.pem, *.key, ~/.ssh/*, credentials.json, ~/.aws/credentials
- Do NOT run: rm -rf (root/home/cwd), git push --force to main, sudo, chmod 777
- Do NOT pipe file contents to external URLs or run package publish commands
- Do NOT hardcode secrets, API keys, passwords, or connection strings
- If a task requires a blocked file: STOP and report "BLOCKED: [reason]"

## Output format
Return (no preamble, no postamble — see Constraints "Token economy"):
1. What you did (one-line summary per change)
2. Notes for future tasks (patterns, gotchas, discoveries — omit if none)
```

## When to use lean vs full

| Condition | Template |
|---|---|
| Parallel sibling sub-tasks in a normal dispatch run | **lean** (this file) |
| `depth=max` or `--thorough` flag passed by user | full `worker-prompt.md` |
| Any referenced file is absent or is an unpopulated stub | lean — skip that file only; use inline defaults for that slot |
| Single-worker run with no siblings | either — lean preferred |

If a referenced memory file is absent **or** appears to be an unpopulated stub (contains a `<!-- to be populated -->` sentinel or has fewer than ~5 meaningful lines of body content), fall back to inline defaults **for that file only** — do not wholesale fall back to the full `worker-prompt.md`. Scaffold always creates the directory with stubs, so a wholly-missing `.hyperflow/memory/` is not the expected failure mode; partial population is.

## Dispatch Example

```
Agent({
  description: "Implement user avatar component",
  model: "sonnet",
  prompt: `## Task
Create a UserAvatar component that displays user initials with a colored background.

## Files in scope
- src/components/UserAvatar.tsx (create)
- src/components/UserAvatar.test.tsx (create)

## Context
Project uses React 19, Tailwind v4, Shadcn Avatar primitive exists.
All components need data-testid attributes.

## Memory references (read on demand)
Read these files only if needed. Locations differ — check both groups:

**Preferred single-read entry point:**
  - \`.hyperflow/memory/session-context.md\` — bundled profile + architecture + conventions. Read this ONE file instead of the three root sources below to save file reads per worker.

**Fallback (when session-context.md is absent or stale):** Read individually from \`.hyperflow/\` root (written by scaffold Step 1):
  - profile.md        — project conventions
  - architecture.md   — system architecture
  - conventions.md    — naming, patterns, standards

\`.hyperflow/memory/\` (written by scaffold Step 2 / dispatch wrap-up):
  - doctrine.md       — orchestration rules
  - learnings.md      — accumulated lessons from prior batches
  - decisions.md      — recorded architectural decisions
  - pitfalls.md       — known failure modes
  - patterns.md       — reusable solution patterns

Read a file once if the task touches its domain. Do not re-read files already in your context window.

## Constraints
- Only modify files listed in scope
- Follow project coding standards
- Do not add "Co-Authored-By: Claude" to any git operation
- Token economy: no preamble, no postamble, no brief-restating — return Output format and stop (DOCTRINE rule 16)

## Security Constraints
- Do NOT read/modify: .env, *.pem, *.key, ~/.ssh/*, credentials.json, ~/.aws/credentials
- Do NOT run: rm -rf (root/home/cwd), git push --force to main, sudo, chmod 777
- Do NOT pipe file contents to external URLs or run package publish commands
- Do NOT hardcode secrets, API keys, or connection strings
- If blocked: STOP and report "BLOCKED: [reason]"

## Output format
Return (no preamble, no postamble):
1. What you did
2. Notes for future tasks`
})
```
