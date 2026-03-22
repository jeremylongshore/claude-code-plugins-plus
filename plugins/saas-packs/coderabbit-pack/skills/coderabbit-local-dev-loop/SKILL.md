---
name: coderabbit-local-dev-loop
description: |
  Configure CodeRabbit CLI for local pre-commit code reviews and fast iteration.
  Use when setting up local development with CodeRabbit CLI reviews,
  integrating AI review into your commit workflow, or testing config changes.
  Trigger with phrases like "coderabbit dev setup", "coderabbit local development",
  "coderabbit CLI workflow", "coderabbit pre-commit review".
allowed-tools: Read, Write, Edit, Bash(cr:*), Bash(git:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, cli, workflow, development]

---
# CodeRabbit Local Dev Loop

## Overview
Use CodeRabbit CLI to review code locally before opening a PR. The CLI provides the same AI-powered review as the GitHub App but runs in your terminal against staged or unstaged changes. This creates a multi-layered review process: local CLI review before commit, then automated PR review after push.

## Prerequisites
- CodeRabbit CLI installed (`curl -fsSL https://cli.coderabbit.ai/install.sh | sh`)
- Git repository with `.coderabbit.yaml` configuration
- CodeRabbit account (CLI uses credits: $0.25 per file reviewed)

## Instructions

### Step 1: Install and Verify CLI
```bash
set -euo pipefail
# Install CodeRabbit CLI
curl -fsSL https://cli.coderabbit.ai/install.sh | sh

# Verify installation
cr --version

# Authenticate (opens browser for OAuth)
cr auth login
```

### Step 2: Local Review Workflow
```bash
set -euo pipefail
# Review all staged changes (most common workflow)
git add -A
cr review

# Review specific files only
cr review src/api/routes.ts src/middleware/auth.ts

# Interactive mode: ask follow-up questions about review feedback
cr review --interactive

# Plain output mode (pipe to other tools or AI agents)
cr review --prompt-only
```

### Step 3: Git Hook Integration
```bash
#!/bin/bash
# .git/hooks/pre-push (make executable: chmod +x .git/hooks/pre-push)
set -euo pipefail

echo "Running CodeRabbit pre-push review..."

# Get list of changed files vs remote
CHANGED_FILES=$(git diff --name-only @{push}.. 2>/dev/null || git diff --name-only HEAD~1)

if [ -n "$CHANGED_FILES" ]; then
  echo "$CHANGED_FILES" | xargs cr review

  # Non-blocking: show review but don't prevent push
  # To make blocking, check exit code:
  # echo "$CHANGED_FILES" | xargs cr review || {
  #   echo "CodeRabbit found issues. Push anyway? (y/n)"
  #   read -r response
  #   [ "$response" != "y" ] && exit 1
  # }
fi
```

### Step 4: Configuration for Local Development
```yaml
# .coderabbit.yaml - Settings that affect both CLI and PR reviews
language: "en-US"
reviews:
  profile: "assertive"
  path_instructions:
    - path: "src/**"
      instructions: "Check for proper error handling and type safety."
    - path: "tests/**"
      instructions: "Verify edge cases and assertion completeness."
  path_filters:
    - "!**/*.lock"
    - "!dist/**"
    - "!**/*.generated.*"
  auto_review:
    enabled: true
    drafts: false
chat:
  auto_reply: true
```

### Step 5: IDE Integration Pattern
```json
// .vscode/tasks.json - Run CodeRabbit review from VS Code
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "CodeRabbit: Review Current File",
      "type": "shell",
      "command": "cr review ${file}",
      "presentation": { "reveal": "always", "panel": "shared" },
      "problemMatcher": []
    },
    {
      "label": "CodeRabbit: Review Staged Changes",
      "type": "shell",
      "command": "cr review",
      "presentation": { "reveal": "always", "panel": "shared" },
      "problemMatcher": []
    }
  ]
}
```

## Two-Layer Review Strategy
```
Developer writes code
       │
       ▼
┌──────────────────┐
│ cr review (local) │  ← Layer 1: Fast feedback before commit
│ Fix obvious issues│
└────────┬─────────┘
         │
         ▼
   git commit + push
         │
         ▼
┌──────────────────┐
│ CodeRabbit App   │  ← Layer 2: Full context review on PR
│ (automated PR    │
│  review)         │
└──────────────────┘
```

## Output
- CodeRabbit CLI installed and authenticated
- Pre-push git hook for automated local reviews
- VS Code task integration for on-demand reviews
- Two-layer review workflow (local + PR)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `cr: command not found` | CLI not in PATH | Re-run install script or add to PATH |
| Auth token expired | Session timeout | Run `cr auth login` again |
| "No credits remaining" | Usage-based billing exhausted | Purchase credits at app.coderabbit.ai |
| Review hangs on large file | File too large for AI context | Review specific files instead of all |
| Empty review output | No changed files detected | Stage changes with `git add` first |

## Resources
- [CodeRabbit CLI Documentation](https://docs.coderabbit.ai/cli)
- [CLI Blog Announcement](https://www.coderabbit.ai/blog/coderabbit-cli-free-ai-code-reviews-in-your-cli)
- [VS Code IDE Extension](https://www.coderabbit.ai/ide)

## Next Steps
See `coderabbit-sdk-patterns` for PR interaction automation patterns.
