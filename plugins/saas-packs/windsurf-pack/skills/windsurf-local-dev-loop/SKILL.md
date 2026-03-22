---
name: windsurf-local-dev-loop
description: |
  Configure Windsurf local development workflow with Cascade, Previews, and terminal integration.
  Use when setting up a development environment, configuring Turbo mode,
  or establishing a fast iteration cycle with Windsurf AI.
  Trigger with phrases like "windsurf dev setup", "windsurf local development",
  "windsurf dev environment", "windsurf workflow", "develop with windsurf".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, workflow, development, turbo-mode]

---
# Windsurf Local Dev Loop

## Overview
Set up a fast, AI-augmented local development workflow using Windsurf's Cascade, Turbo mode, Previews, and terminal integration. The goal is a tight loop: edit with Cascade, preview in-IDE, iterate, test, commit.

## Prerequisites
- Windsurf authenticated and project open
- Node.js 18+ or Python 3.10+
- Git initialized in project

## Instructions

### Step 1: Create .windsurfrules for Project Context

```markdown
<!-- .windsurfrules - placed at project root, committed to git -->

# Project: my-app

## Stack
- Language: TypeScript (strict mode)
- Framework: Next.js 14 (App Router)
- Styling: Tailwind CSS v3
- Testing: Vitest + Testing Library
- Package manager: pnpm

## Architecture
- Server Components by default
- Client Components only when state/interactivity needed
- API routes in app/api/
- Business logic in lib/services/
- Types in lib/types/

## Conventions
- Named exports, never default
- async/await, never raw .then()
- zod for all runtime validation
- Error handling: Result pattern in services
```

### Step 2: Configure .codeiumignore

```gitignore
# .codeiumignore - exclude from AI indexing (same syntax as .gitignore)
node_modules/
.next/
dist/
build/
coverage/
*.min.js
*.map
.env
.env.*
```

### Step 3: Set Up Turbo Mode for Fast Terminal Execution

Turbo mode lets Cascade auto-execute terminal commands without asking permission for each one.

**Enable:** Windsurf Settings > Cascade > Terminal Execution Level > Turbo

**Configure safety lists:**
```json
// Settings (JSON) — search "cascadeCommands"
{
  "windsurf.cascadeCommandsAllowList": [
    "npm", "pnpm", "npx", "node", "tsc",
    "vitest", "jest", "eslint", "prettier",
    "git status", "git diff", "git log", "git add"
  ],
  "windsurf.cascadeCommandsDenyList": [
    "rm -rf", "sudo", "git push --force",
    "git reset --hard", "DROP TABLE", "shutdown"
  ]
}
```

### Step 4: Use Previews for UI Development

Ask Cascade to preview your web app:
```
"Start the dev server and preview the app"
```

Cascade starts the server and opens an in-IDE Preview tab. From the Preview:
- Click **"Send element"** (bottom-right) to select a UI element and send it to Cascade
- Console errors are automatically forwarded to Cascade for debugging
- Iterate by describing changes: "Make the header sticky and add a dark mode toggle"

### Step 5: The Dev Loop

```
1. Open Cascade (Cmd/Ctrl+L)
2. Describe the feature or fix
3. Cascade edits files and runs commands (Turbo mode)
4. Preview updates in-IDE (hot reload)
5. Click broken elements → send to Cascade
6. Cascade fixes → repeat until correct
7. Run tests: "Run vitest for the files you changed"
8. Commit: "Commit these changes with message: add dark mode toggle"
```

### Step 6: Terminal Integration

Use Cmd/Ctrl+I in the terminal for natural language commands:
```
Type: "find all files importing the Button component"
Windsurf generates: grep -rl "import.*Button" src/

Type: "run tests for auth module only"
Windsurf generates: npx vitest run src/auth/
```

Highlight terminal errors and press Cmd/Ctrl+L to send to Cascade for diagnosis.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade not seeing project context | No `.windsurfrules` | Create rules file at project root |
| Slow AI suggestions | Large repo indexed | Add `.codeiumignore` |
| Turbo mode running dangerous commands | Missing deny list | Configure `cascadeCommandsDenyList` |
| Preview not loading | Dev server not started | Ask Cascade to start it first |
| Hot reload not working | Preview disconnected | Close and re-open Preview tab |

## Examples

### Quick Project Bootstrap
```
Cascade prompt: "Initialize a new Next.js 14 project with TypeScript,
Tailwind CSS, and Vitest. Set up the folder structure matching
our .windsurfrules conventions."
```

### Debug-Fix Loop
```
1. See error in terminal or Preview console
2. Highlight error text → Cmd/Ctrl+L → "Fix this error"
3. Cascade reads error, finds root cause, applies fix
4. Preview auto-reloads → verify fix
```

## Resources
- [Windsurf Terminal Docs](https://docs.windsurf.com/windsurf/terminal)
- [Windsurf Previews](https://docs.windsurf.com/windsurf/previews)
- [Cascade Overview](https://docs.windsurf.com/windsurf/cascade/cascade)

## Next Steps
See `windsurf-sdk-patterns` for workspace configuration patterns.
