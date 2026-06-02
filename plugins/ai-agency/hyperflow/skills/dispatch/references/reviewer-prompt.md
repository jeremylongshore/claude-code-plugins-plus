# Reviewer Prompt Template

Use this template when dispatching Opus reviewers via the Agent tool. Review depth scales by task complexity.

## Complexity Classification

Opus determines complexity BEFORE dispatching the reviewer:

- **Simple** (levels 1-2): Single file, rename, config, one-line fix
- **Medium** (levels 1-3): 2-3 files, modifies existing functionality, touches shared code
- **Complex** (levels 1-5): 4+ files, new feature, UI work, DB/API changes

## Template

```
## Review scope
[Files changed, task assigned, complexity classification]

## Worker output
[Paste worker's summary]

## Level 1: Requirements
- Does the output match the task spec exactly?
- All sub-tasks completed? Nothing missing?
- Nothing extra added beyond the spec?

## Level 2: Code Quality
- Follows project naming conventions?
- No TypeScript `any`, no dead code?
- Uses existing utils/hooks (not reinventing)?
- Proper error handling, SRP, early returns?

## Level 3: Integration (medium + complex only)
- Imports resolve? No circular dependencies?
- Shared state/context not broken?
- API contracts preserved?
- Existing tests would still pass?

## Level 4: Performance & Security (complex only)
- No N+1 queries? Expensive ops memoized?
- No unnecessary re-renders?
- No hardcoded secrets (sk-*, AKIA*, ghp_*, private keys)?
- Input validation at boundaries? No injection vectors?

## Level 5: UX & Accessibility (complex UI tasks only)
- Aria labels on interactive elements?
- Keyboard navigation works?
- Loading/error/empty states handled?
- Responsive + RTL considered?

## Security Review (always)
- Were any blocked files accessed? (.env, *.pem, *.key, ~/.ssh/*)
- Any dangerous commands? (rm -rf, force push, sudo)
- Any data exfiltration? (contents piped to external URLs)

## Output format
```
── Review ──────────────────────────────
L1 Requirements    pass     — [summary]
L2 Code Quality    pass     — [summary]
L3 Integration     pass     — [summary]
L4 Performance     fail     — [issue found]
L5 UX/A11y         skipped  — not applicable
────────────────────────────────────────
VERDICT: APPROVED | NEEDS_FIX | SECURITY_VIOLATION
[Issues per failed level]
[Notes for future tasks]
```
```

## Dispatch Example

```
Agent({
  description: "Review auth middleware (complex)",
  model: "opus",
  prompt: `## Review scope
Files: src/middleware/auth.ts, src/middleware/auth.test.ts, src/types/auth.ts, src/types/session.ts
Task: Create JWT auth middleware with refresh logic
Complexity: Complex (4 files, new feature, security-sensitive)

## Worker output
1. Created auth middleware with RS256 verification
2. Added refresh token rotation
3. Tests cover valid/expired/malformed tokens

## Level 1: Requirements
- JWT validation with RS256? Refresh logic? Rate limiting?

## Level 2: Code Quality
- Follows conventions? Types correct? No any?

## Level 3: Integration
- Works with existing route handlers? Session types compatible?

## Level 4: Performance & Security
- No secrets hardcoded? Token validation safe? Timing attacks prevented?

## Level 5: UX & Accessibility
- Skipped (not a UI task)

## Security Review
- Blocked files? Secrets? Dangerous commands?

## Output format
── Review ──
pass / fail / skipped per level + VERDICT`
})
```

See [review-levels.md](review-levels.md) for full checklist details and failure handling.
