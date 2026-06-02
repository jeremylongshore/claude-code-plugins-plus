# Quality Gates

Automated checks that must pass before a worker's output is approved. Runs after Opus code review, before marking a task done.

## Flow

```
Worker completes
    |
[Opus] Reviews code quality
    |
[Opus] Runs quality gates
    |
All green? -> Mark task done
    |
Red? -> Send failures back to worker -> worker fixes -> re-run gates
```

## Checks

Opus auto-detects which checks are available by scanning the project's package.json scripts and config files.

| Check | Detection | Command |
|-------|-----------|---------|
| Lint | `eslint.config.*` or `scripts.lint` | `pnpm lint` / `npm run lint` |
| Typecheck | `tsconfig.json` | `pnpm typecheck` / `npx tsc --noEmit` |
| Tests | `vitest.config.*` or `jest.config.*` | `pnpm test` (affected files only) |
| Build | `scripts.build` | `pnpm build` (only on final review) |

## Scope

- **Per-task gates:** Lint + typecheck + tests for affected files only (not full suite)
- **Final review gates:** Full lint + typecheck + build + full test suite

Running the full suite per task is wasteful. Scope checks to what the worker touched.

## Failure Handling

1. Gate fails -> Opus extracts the error message
2. Opus sends specific fix instructions to the worker (same Sonnet instance if possible)
3. Worker fixes -> gates re-run
4. Max 3 retry loops per gate. After 3 failures, Opus escalates to an Opus-model worker
5. If Opus worker also fails, surface the error to the user

## Configuration

To disable specific gates or add custom checks, users can add to their project CLAUDE.md:

```markdown
## Hyperflow Quality Gates
- skip: typecheck
- add: pnpm format --check
```

Or say in conversation: "hyperflow: skip typecheck for this session"

## Worker Prompt Addition

When quality gates are active, append to the worker prompt constraints:

```
## Quality Requirements
- Code must pass lint (eslint)
- Code must pass typecheck (tsc --noEmit)
- Tests must pass for affected files
- Run these yourself before reporting completion
```
