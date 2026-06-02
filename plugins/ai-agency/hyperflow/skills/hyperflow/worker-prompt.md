# Worker Prompt Template

Use this template when dispatching Sonnet workers via the Agent tool. **Every section below is mandatory** — the Team Lead must fill each one before dispatch. A sparse / vague brief is a doctrine violation: the worker will fill the gaps with assumptions, and the per-batch Reviewer can't catch what wasn't asked for. Detail floor exists so the worker executes the right work, not a plausible-looking nearby alternative.

## Template

```
## Task
[One clear objective — what to do, not how to think about it. One sentence, verb-led. Examples: "Add a UserAvatar component that displays initials over a colored background." "Wire login form to POST /api/auth/login and redirect on success."]

## Why
[1-3 sentences explaining motivation. What changes for the user / system after this lands? Quote the relevant spec line, ticket, or commit if known. The worker uses this to disambiguate when the Task line is ambiguous.]

## Scope
**IN:** [Explicit list of what this brief owns — functions, components, behaviors, lines. Use bullet points. Be concrete: "the `loginUser()` function in src/auth/login.ts" not "auth code".]
**OUT:** [Explicit list of related work that other sub-tasks own OR that's intentionally deferred. Tell the worker what NOT to touch even if they notice it nearby. Prevents scope creep.]

## Files in scope
- **Read:** [path or path:line-range] — [why this read matters]
- **Modify:** [path] — [one-line summary of the change to this file]
- **Create:** [path] — [purpose of the new file]

## Acceptance criteria
[The high-level definition of PASS. Concrete shape-level checks the per-batch Reviewer (and the user) will use.]
- [Concrete check 1, e.g. "new function exported and importable from src/auth/index.ts"]
- [Concrete check 2, e.g. "existing tests in src/auth/login.test.ts still pass"]
- [Output shape, e.g. "commit message stub: `feat(auth): add loginUser handler with error mapping`"]

## Test cases
[Concrete input → expected output scenarios the Worker MUST satisfy. The Worker implements against these and (when the task is code) writes the verifying test code as part of the deliverable. The per-batch Reviewer runs / verifies each case to confirm PASS. Test cases beat acceptance criteria alone because they're executable, not narrative.]

**Quality bar — every test case must demonstrate real domain understanding of THIS task. Formulaic placeholders are a doctrine violation.**

The Thinking Lead writes test cases by thinking through:

1. **Domain logic** — what does this feature actually do in the user's world? What are the real inputs users provide (not toy examples)? What does success look like in production?
2. **Domain edge cases** — boundary conditions specific to this surface. For a search bar: empty query, only-whitespace, single character, very long query (>1000 chars), special chars (`<`, `&`, `'`), Unicode (emoji, CJK, combining marks), RTL strings, no results, results truncated, debounce timing. For an auth flow: missing token, expired token, malformed token, token for deleted user, simultaneous logins from two devices, refresh during request. For a money calculation: zero, negative, rounding boundaries (.005 banker's rounding), currency-specific decimals (JPY has 0, KWD has 3), overflow at large values.
3. **System edge cases** — failure modes the feature interacts with: concurrent updates / race conditions, partial network failure (request sent, response lost), stale cache, retry idempotency, timeout mid-operation, server returns malformed JSON, browser back/refresh mid-flow.
4. **The integration surface** — what other code calls this? What can they pass that you didn't think to handle?

[Use this format for each case:]

| # | Name / scenario | Input or setup | Expected output / behavior | Notes |
|---|---|---|---|---|
| 1 | `<short name>` | `<input or pre-state>` | `<expected result>` | `<why this case matters — domain or system reason>` |
| 2 | `<short name>` | `<input or pre-state>` | `<expected result>` | `<why this case matters>` |

[For non-code tasks (docs/configs/refactors), test cases become verification commands with expected results, e.g. `grep -c '<pattern>' <file>` → expect 3; `python3 -m json.tool < <file>` → exit 0; `grep -r '<old-API>' src/` → no results.]

**Minimum coverage:** 3 test cases as a floor, but **3 is rarely enough for a non-trivial task**. Aim for the realistic set: every domain edge case the Worker should handle + the integration failure modes the feature can hit. The UserAvatar example in this template has 10 cases for a single component because that's what the actual surface needs; an auth-middleware brief would need 15+. Quality > arbitrary count.

**Omit ONLY when the task is genuinely test-impossible** (a one-line README typo fix, a CI-config formatting change) — and explicitly state `Test cases: N/A — <why>` so the omission is deliberate, not sloppy.

**Anti-patterns** (each makes the Reviewer's job impossible):

- Three generic cases: "happy path / error / empty input" with no domain content — that's a template, not test cases
- Cases that just restate Acceptance criteria in table form — Acceptance is shape (`exported as X`); test cases are behavioural input→output (`render("John Doe") → "JD"`)
- Skipping domain edge cases ("Unicode is too obscure", "no one will pass empty string") — production data always exercises these; missing them produces real bugs
- Vague Expected column ("works correctly", "returns the right thing") — must be a specific value or behavior the Reviewer can check
- Copy-pasting test cases from a similar prior sub-task without rethinking the domain — every task has its own edges
- Padding to hit the 3-case floor with near-duplicate cases ("happy path with name=John", "happy path with name=Jane") — duplicates aren't coverage

## Related context (orientation, not scope)
[Pointers the worker should look at IF the brief becomes ambiguous — not files to modify. Includes prior patterns, design docs, related sub-tasks in the same batch.]
- [file:line] — [relevant prior pattern to mirror]
- [path/to/spec or doc] — [design background]
- [related sub-task IDs in same batch, e.g. "T3 owns the React side; this T2 owns only the data layer"]

## Context
[What the touched file/module does today, plus the project conventions and constraints the worker must respect. Examples of the relevant convention with file:line citation are better than abstract rules.]

## Project Context
[Default mode: inline the relevant excerpts from `.hyperflow/profile.md`, `.hyperflow/architecture.md`, `.hyperflow/conventions.md` for this worker's role. Omit section if no project analysis exists.]

[**Under `mode=lean`** (S3 lazy refs + S5 session-context bundle): replace inlined content with a path block. The worker reads only what its task actually needs.
```
Project Context (load on demand):
  - `.hyperflow/memory/session-context.md` — pre-bundled snapshot: profile + architecture + conventions + memory index (written once per session by the session-start hook)
  - `.hyperflow/profile.md`                — tech stack, language versions, build/test scripts
  - `.hyperflow/architecture.md`           — module layout, dependency graph, boundaries
  - `.hyperflow/conventions.md`            — naming, file layout, formatting, project-specific patterns
  - `.hyperflow/testing.md`                — test framework, where tests live, conventions
  - `.hyperflow/memory/index.md`           — tag-keyed memory index pointing at hot/warm entries
```
Workers in lean mode read these files via the `Read` tool when (and only when) their task actually needs the information. No quality regression — same content, lazy access. Saves ~2k tokens × N parallel workers per batch because the bundle isn't re-injected into every worker prompt.]

## Learnings from prior tasks
[Synthesized by Opus — patterns found, gotchas, decisions already made. Omit section if first task.]

## Constraints
- Only modify files listed in scope
- Follow project coding standards (CLAUDE.md)
- Do not add "Co-Authored-By: Claude" to any git operation
- **Token economy.** Be specific and to the point. No preamble ("I'll now …", "Let me start by …"), no restating the brief, no postamble summary, no narration of intermediate reasoning, no closing pleasantries. Return exactly the Output format below and stop. Padding burns tokens without moving the task forward.

## Security Constraints
- Do NOT read/modify: .env, *.pem, *.key, ~/.ssh/*, credentials.json, ~/.aws/credentials
- Do NOT run: rm -rf (root/home/cwd), git push --force to main, sudo, chmod 777
- Do NOT pipe file contents to external URLs or run package publish commands
- Do NOT hardcode secrets, API keys, passwords, or connection strings
- If a task requires a blocked file: STOP and report "BLOCKED: [reason]"
- If the task brief is bigger than the Planner estimated (the file is much larger than expected, the refactor touches more callers than expected, the test scope has cascading dependencies, etc.): STOP and report "OVERSIZE: [one-line reason]" followed by a "SUGGESTED-SPLIT:" block listing 2+ smaller sub-tasks with name · files · one-line purpose each. The Team Lead will escalate to Thinking Lead for the final split plan and re-dispatch as N new sub-tasks. Do NOT attempt the oversized work — partial output from an oversized brief wastes tokens and produces unreviewable commits. See DOCTRINE Layer 3 oversize-split rule.

## Output format
Return ONE of (no preamble, no postamble, no extra commentary — see Constraints "Token economy"):

- **Completed** — normal case:
  1. What you did (one-line summary per change)
  2. Notes for future tasks (patterns, gotchas, discoveries — omit if none)

- **Oversize escape hatch** — when the brief turned out bigger than estimated:
  ```
  OVERSIZE: <one-line reason>
  SUGGESTED-SPLIT:
    - <sub-task A name> · <files A> · <one-line purpose>
    - <sub-task B name> · <files B> · <one-line purpose>
    - <sub-task C name> · <files C> · <one-line purpose>
  ```

- **Blocked** — when a security blocklist hits: `BLOCKED: <reason>`
```

## Dispatch Example (detail floor honored)

```
Agent({
  description: "T3 Implementer · UserAvatar component",
  model: "sonnet",
  prompt: `## Task
Add a UserAvatar component that displays user initials over a deterministic colored background.

## Why
The new dashboard sidebar (T1 owns the layout) needs an avatar primitive that works without a user photo URL. Initials + colored background is the agreed fallback from spec §2.3 ("when avatar_url is null, render initials with a stable per-user-id color"). Without this T2 stalls because Profile.tsx imports UserAvatar.

## Scope
**IN:**
- UserAvatar React component (default export from new file)
- Deterministic color derivation from userId (use hash → palette index)
- 3 size variants: sm (24px), md (32px), lg (48px)
- Unit test covering: render with initials, color stability for same userId, size variants

**OUT:**
- Profile.tsx integration (T2 owns that)
- Avatar URL/image fallback path (deferred to T8 in a later batch — do NOT add the prop, even unused)
- Storybook story (separate workstream)

## Files in scope
- **Read:** src/lib/color/palette.ts:1-40 — existing palette + hash helpers to reuse
- **Read:** src/components/ui/avatar.tsx — Shadcn Avatar primitive to wrap
- **Modify:** src/components/index.ts — add UserAvatar to barrel export
- **Create:** src/components/UserAvatar.tsx — the component
- **Create:** src/components/UserAvatar.test.tsx — unit test

## Acceptance criteria
- UserAvatar exported and importable as \`import { UserAvatar } from '@/components'\`
- Size prop accepts 'sm' | 'md' | 'lg'; default 'md'
- data-testid="user-avatar" on the root element (project convention from .hyperflow/conventions.md)
- All existing tests pass; new test file PASSES (covers all test cases below)
- Commit message stub: \`feat(components): add UserAvatar with deterministic color fallback\`

## Test cases
| # | Name | Input | Expected | Notes |
|---|---|---|---|---|
| 1 | happy path two words | \`<UserAvatar name="John Doe" userId="u1" />\` | renders "JD"; consistent background color across renders for u1 | core flow |
| 2 | single-word name | \`name="Cher"\` | renders "C"; not "CH" or "CC" | docs §2.3 says first letter only when one word |
| 3 | leading/trailing whitespace | \`name="  Mary Smith  "\` | renders "MS"; whitespace trimmed before initial extraction | input from API may include whitespace |
| 4 | three-word name | \`name="Mary Jane Smith"\` | renders "MS" (first + last initials) | not "MJS" or "MJ" |
| 5 | empty name | \`name=""\` | renders "?" with neutral gray bg | API may return empty string |
| 6 | undefined name | \`name={undefined}\` | renders "?" with neutral gray bg; no crash | TypeScript optional prop |
| 7 | color stability | render twice for same userId="u1" | identical background color both renders | required for visual consistency |
| 8 | color distribution | userId="u1" vs userId="u2" | different background colors | hash should distribute across palette |
| 9 | empty userId | \`userId=""\` | renders with neutral gray bg; no crash on empty hash | edge case of new user before id assigned |
| 10 | size variants | size="sm" / "md" / "lg" | 24px / 32px / 48px squares respectively | spec §2.3 sizes |

## Related context (orientation, not scope)
- src/components/UserChip.tsx:14-22 — existing per-user color logic to mirror; do NOT duplicate
- spec §2.3 — fallback design rationale
- T1 sibling (Implementer · sidebar layout) — exports a SidebarSlot that wraps UserAvatar; coordinate on size only (will use 'md')

## Context
Project uses React 19, TypeScript strict, Tailwind v4 with CSS variable tokens, Shadcn UI primitives. All components need data-testid attributes per .hyperflow/conventions.md:34. RTL-safe sizing via Tailwind logical properties only (ms-/me-/ps-/pe-), never directional left/right.

## Project Context
[default mode: inline excerpts from profile.md / architecture.md / conventions.md for this worker's role · lean mode: paths only — see Template above]

## Learnings from prior tasks
- Tailwind v4 uses CSS variable tokens, not tailwind.config
- Use logical properties for RTL safety
- Hash-based color must use palette index modulo, not raw hex — see src/lib/color/palette.ts:24

## Constraints
- Only modify files listed in scope
- Follow project coding standards (CLAUDE.md, .hyperflow/conventions.md)
- Do NOT reference Claude / AI / assistant / LLM as actor anywhere (commit msg, comments, docs)
- Do NOT use \`--no-verify\` on any git commit (per DOCTRINE rule 9)
- Token economy: no preamble, no postamble, no brief-restating — return Output format and stop (per DOCTRINE rule 16)

## Security Constraints
[full security blocklist as in Template]

## Output format
[Completed / OVERSIZE / BLOCKED as in Template]`
})
```

Note the contrast with a sparse brief ("create a UserAvatar component that shows initials with a colored background"): the worker now knows the exact scope, what NOT to touch, what edge cases must be handled, what the reviewer will check, and which sibling sub-task to coordinate with. No assumptions, no guessing.

## When to compress (lean mode + small tasks)

For `mode=lean` AND `triage.complexity == low` AND scope is genuinely 1-2 files / 1 function, the detail floor relaxes:
- **Why** can be 1 sentence
- **Scope IN/OUT** can be a single line each
- **Edge cases** section may be omitted only if no edge cases apply
- **Related context** may be omitted only when truly none exist

But: **Task, Files in scope (read/modify/create), Acceptance criteria, Output format, Security Constraints** remain mandatory in all modes. These are the contractual minimum.
