---
name: windsurf-known-pitfalls
description: |
  Identify and avoid Windsurf anti-patterns and common integration mistakes.
  Use when reviewing Windsurf code for issues, onboarding new developers,
  or auditing existing Windsurf integrations for best practices violations.
  Trigger with phrases like "windsurf mistakes", "windsurf anti-patterns",
  "windsurf pitfalls", "windsurf what not to do", "windsurf code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Known Pitfalls

## Overview
Real gotchas when using Windsurf (Codeium's AI IDE). Windsurf's Cascade AI agent, Flows architecture, and workspace indexing behave differently from VS Code copilots -- understanding these differences prevents frustrating debugging sessions.

## Prerequisites
- Windsurf installed and configured
- Understanding of Cascade's agent model vs inline autocomplete
- Awareness of workspace indexing behavior

## Instructions

### Step 1: Don't Confuse Cascade with Autocomplete

Windsurf has two AI systems: Cascade (agentic, multi-file) and Supercomplete (inline). Using Cascade for quick completions wastes context.

```
# BAD: opening Cascade to complete a single line
User: "finish this function signature"
# Cascade spins up full agent context, reads multiple files = slow

# GOOD: use Tab for inline Supercomplete, Cascade for multi-step tasks
# Supercomplete: just type and press Tab
# Cascade: Cmd+L for multi-file refactoring, debugging, architecture
```

### Step 2: Manage Cascade Context Window

Cascade reads your entire workspace to build context. Large monorepos with node_modules or build artifacts slow it down.

```
# BAD: no .windsurfignore in a large monorepo
# Cascade indexes node_modules, dist/, .git/ = slow and noisy context

# GOOD: create .windsurfignore (same syntax as .gitignore)
# .windsurfignore
node_modules/
dist/
build/
.next/
*.min.js
*.bundle.js
coverage/
```

### Step 3: Avoid Overly Broad Cascade Instructions

Vague instructions cause Cascade to make sweeping changes across many files.

```
# BAD: "refactor the codebase to use TypeScript"
# Cascade may try to convert every file at once

# GOOD: scope the task
"Convert src/utils/api.js to TypeScript. Add proper types for all
function parameters and return values. Don't change other files."
```

### Step 4: Trust But Verify File Edits

Cascade can write directly to files. Not reviewing diffs before accepting leads to subtle bugs.

```
# BAD: accepting all Cascade changes without review
# Cascade modified 12 files -> "Accept All" -> broken tests

# GOOD: review each file change in the diff view
# 1. Read the Cascade output explaining what it changed
# 2. Review each file diff individually
# 3. Accept file by file, or reject problematic changes
# 4. Run tests before committing
```

### Step 5: Handle Extension Compatibility

Windsurf is VS Code-based but not all extensions work. Some conflict with Cascade.

```
# KNOWN CONFLICTS:
# - GitHub Copilot: conflicts with Supercomplete (disable one)
# - Other AI assistants: may interfere with Cascade context
# - Some language servers: duplicate suggestions

# GOOD: disable competing AI extensions
# Settings > Extensions > disable Copilot if using Windsurf AI
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade is slow | Large workspace indexed | Add `.windsurfignore` |
| Wrong file modified | Ambiguous instruction | Be specific about file paths |
| Conflicting completions | Multiple AI extensions | Disable competing extensions |
| Cascade loses context | Very long conversation | Start fresh Cascade session |
| Edits break build | Accepted without review | Always review diffs, run tests |

## Examples

### Effective Cascade Prompts
```
GOOD: "In src/api/routes.ts, add input validation for the POST /users
endpoint using zod. Validate email format and name length (2-50 chars).
Return 400 with specific error messages on validation failure."  # HTTP 400 Bad Request

BAD: "Add validation to the API"
```

## Resources
- [Windsurf Docs](https://docs.windsurf.com)
- [Cascade Guide](https://docs.windsurf.com/cascade)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale