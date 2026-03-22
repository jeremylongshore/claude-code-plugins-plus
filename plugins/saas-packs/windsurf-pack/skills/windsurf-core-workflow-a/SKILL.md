---
name: windsurf-core-workflow-a
description: |
  Execute Windsurf's primary workflow: Cascade Write mode for multi-file agentic coding.
  Use when building features, refactoring across files, or performing complex code tasks.
  Trigger with phrases like "windsurf cascade write", "windsurf agentic coding",
  "windsurf multi-file edit", "cascade write mode", "windsurf build feature".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, cascade, write-mode, agentic]

---
# Windsurf Core Workflow A — Cascade Write Mode

## Overview
Cascade Write mode is Windsurf's primary productivity tool. It acts as an autonomous agent that can create files, modify code across multiple files, run terminal commands, install dependencies, and debug errors -- all from a single natural language prompt. This is the "money-path" workflow for Windsurf users.

## Prerequisites
- Windsurf IDE with Cascade enabled
- `.windsurfrules` configured (see `windsurf-sdk-patterns`)
- Git initialized with clean working tree

## Instructions

### Step 1: Create a Git Checkpoint

Always commit or stash before a Cascade session. Cascade writes directly to your files.

```bash
git add -A && git commit -m "checkpoint: before cascade session"
# Or for uncommitted work:
git stash push -m "pre-cascade stash"
```

### Step 2: Open Cascade in Write Mode

Press **Cmd/Ctrl+L** to open the Cascade panel. Ensure "Write" mode is selected (not "Chat"). Write mode allows Cascade to:

- Create and modify files
- Run terminal commands (with Turbo or per-command approval)
- Install dependencies
- Read terminal output for debugging
- Open browser previews

### Step 3: Write an Effective Prompt

Structure your prompt with scope, specifics, and constraints:

```
"In src/services/, create a NotificationService that:
1. Sends email via Resend API (already in package.json)
2. Sends Slack messages via webhook URL from env
3. Uses the Result<T,E> pattern from src/types/result.ts
4. Includes retry logic with exponential backoff (max 3 retries)
5. Add unit tests in tests/services/notification.test.ts
Don't modify any existing files except to add exports."
```

### Step 4: Review Cascade's Plan and Execution

Cascade shows its reasoning and plan before executing:

```
Cascade output flow:
1. "I'll create the notification service with email and Slack support..."
2. Creates src/services/notification.ts (shows diff)
3. Creates tests/services/notification.test.ts (shows diff)
4. Runs: npm install resend (if needed)
5. Runs: npx vitest run tests/services/notification.test.ts
6. Reports results
```

**Review each file diff in the Cascade output.** You can:
- **Revert** individual steps by hovering over a step and clicking the revert arrow
- **Revert all** to return to the state before the Cascade session
- Create named **checkpoints** for complex multi-step sessions

### Step 5: Iterate on Errors

If tests fail, Cascade retains context about what it just did:

```
"The test for sendSlack is failing with 'fetch is not defined'.
Fix it by using the node:test built-in fetch mock."
```

Cascade reads the error, understands its own recent changes, and applies targeted fixes.

### Step 6: Use @ Mentions for Precision

```
@src/types/result.ts — force Cascade to read this file for the Result pattern
@src/services/       — reference the entire services directory for consistency
@web resend API docs  — search the web for current Resend documentation
```

## Output
- Multi-file code changes applied by Cascade
- Terminal commands executed (installs, tests, builds)
- Test results confirming implementation correctness
- Reviewable diffs for every file change

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade modifies wrong files | Vague prompt | Specify exact file paths and constraints |
| Changes break existing tests | No constraint on existing code | Add "don't modify existing files" to prompt |
| Cascade loops on error | Insufficient context | Paste the full error message, reference relevant files |
| Write mode not available | On Free plan with no credits | Check credit balance at windsurf.com/account |
| Cascade ignores .windsurfrules | Rules file > 6,000 chars | Trim rules or split into workspace rules |

## Examples

### Full-Stack Feature
```
"Add a user profile page:
1. Create app/profile/page.tsx as a Server Component
2. Create app/profile/edit/page.tsx as a Client Component with form
3. Add GET /api/profile and PUT /api/profile route handlers
4. Use the existing UserSchema from lib/types/user.ts for validation
5. Style with Tailwind matching the existing design system
6. Add tests for both API routes"
```

### Refactoring Task
```
"Extract the authentication logic from src/middleware/auth.ts into:
- src/services/auth.ts (JWT validation, token refresh)
- src/services/session.ts (session management)
Update all imports across the codebase. Run tests after."
```

## Resources
- [Cascade Write Mode](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Cascade Checkpoints](https://docs.windsurf.com/windsurf/cascade/cascade)

## Next Steps
For configuration management workflow, see `windsurf-core-workflow-b`.
