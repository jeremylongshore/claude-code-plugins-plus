---
name: windsurf-reliability-patterns
description: |
  Implement Windsurf reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Windsurf integrations, implementing retry strategies,
  or adding resilience to production Windsurf services.
  Trigger with phrases like "windsurf reliability", "windsurf circuit breaker",
  "windsurf idempotent", "windsurf resilience", "windsurf fallback", "windsurf bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Reliability Patterns

## Overview
Reliability patterns for Windsurf AI IDE workflows. Windsurf's Cascade agent can modify multiple files simultaneously, making reliable workflows dependent on proper checkpointing, review, and rollback strategies.

## Prerequisites
- Windsurf installed with Cascade enabled
- Git repository for version control
- Understanding of Cascade's multi-file editing model

## Instructions

### Step 1: Commit Before Cascade Sessions

Always create a clean git checkpoint before asking Cascade to make changes.

```bash
# Before starting a Cascade session
git add -A && git commit -m "checkpoint: before cascade refactor"

# Now ask Cascade to make changes
# If results are bad:
git diff               # review what changed
git checkout -- .      # revert everything
# Or keep good changes:
git add specific-file.ts && git commit -m "cascade: extracted service layer"
```

### Step 2: Scope Cascade Tasks Narrowly

Large tasks cause Cascade to make sweeping changes that are hard to review.

```
# BAD: too broad
"Refactor the authentication system"
# Cascade may modify 30+ files

# GOOD: incremental, reviewable steps
Step 1: "Extract the JWT validation logic from src/middleware/auth.ts
         into a new src/services/jwt.ts module"
Step 2: "Update src/middleware/auth.ts to import from src/services/jwt.ts"
Step 3: "Add unit tests for src/services/jwt.ts"
```

### Step 3: Validate After Each Cascade Edit

Run tests and type checks after every Cascade modification.

```bash
set -euo pipefail
# After accepting Cascade changes
npm run typecheck     # catch type errors from refactoring
npm test              # verify existing behavior preserved
npm run lint          # check code style

# If any fail, ask Cascade to fix:
# "The typecheck failed with: [paste error]. Fix the type error in src/services/jwt.ts"
```

### Step 4: Use .windsurfignore for Workspace Performance

Large workspaces slow down Cascade's context building. Exclude build artifacts.

```gitignore
# .windsurfignore
node_modules/
dist/
build/
.next/
coverage/
*.min.js
*.map
__pycache__/
.venv/
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade broke the build | Accepted changes without testing | Git revert, run tests after each edit |
| Cascade modified wrong files | Ambiguous instructions | Specify exact file paths in prompt |
| Slow Cascade responses | Large workspace indexed | Add `.windsurfignore` |
| Lost good changes | Reverted too broadly | Commit incrementally, use `git stash` |

## Examples

### Safe Cascade Workflow
```bash
set -euo pipefail
git stash                          # save WIP
git checkout -b cascade/refactor   # new branch
# Ask Cascade to make changes
npm test && git add -A && git commit -m "cascade: refactored auth"
# If bad: git checkout main && git branch -D cascade/refactor
```

## Resources
- [Windsurf Docs](https://docs.windsurf.com)
- [Cascade Best Practices](https://docs.windsurf.com/cascade)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale