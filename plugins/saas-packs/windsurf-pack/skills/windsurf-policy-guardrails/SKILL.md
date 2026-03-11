---
name: windsurf-policy-guardrails
description: |
  Implement Windsurf lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Windsurf integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Windsurf best practices.
  Trigger with phrases like "windsurf policy", "windsurf lint",
  "windsurf guardrails", "windsurf best practices check", "windsurf eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Windsurf Policy Guardrails

## Overview
Policy guardrails for Windsurf AI IDE usage in team environments. Cascade's ability to modify multiple files autonomously requires policies around code review, workspace isolation, and AI-generated code quality.

## Prerequisites
- Windsurf configured for team use
- Git workflow established
- Code review process in place

## Instructions

### Step 1: Mandatory Review for AI-Generated Code

Cascade can modify many files at once. Enforce review before merging.

```yaml
# .github/workflows/cascade-review.yml
name: AI Code Review Gate
on: pull_request

jobs:
  check-ai-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Check for large AI-generated changesets
        run: |
          CHANGED=$(git diff --stat origin/main..HEAD | tail -1 | awk '{print $1}')
          if [ "$CHANGED" -gt 20 ]; then
            echo "::warning::Large changeset ($CHANGED files). Ensure thorough review of AI-generated code."
          fi
      - name: Require tests for new code
        run: |
          NEW_FILES=$(git diff --name-only --diff-filter=A origin/main..HEAD | grep -E '\.(ts|js|py)$' | wc -l)
          TEST_FILES=$(git diff --name-only --diff-filter=A origin/main..HEAD | grep -E '\.test\.|\.spec\.' | wc -l)
          if [ "$NEW_FILES" -gt 3 ] && [ "$TEST_FILES" -eq 0 ]; then
            echo "::error::New source files added without corresponding tests"
            exit 1
          fi
```

### Step 2: Workspace Isolation Rules

Prevent Cascade from accessing sensitive files or directories.

```gitignore
# .windsurfignore - also acts as a security boundary
.env
.env.*
credentials/
secrets/
*.pem
*.key
private/
```

### Step 3: Cascade Usage Guidelines for Teams

```markdown
# Team Windsurf Policy

1. **Always commit before Cascade**: Create a checkpoint before AI edits
2. **One task per Cascade session**: Don't combine refactor + feature
3. **Review every file change**: Don't "Accept All" without reading diffs
4. **Run tests after accepting**: `npm test` before committing
5. **Tag AI-generated commits**: Use `[cascade]` prefix in commit messages
6. **No Cascade on main/prod**: Only use on feature branches
```

### Step 4: Extension Trust Policy

Control which extensions are allowed alongside Windsurf's AI.

```json
// .vscode/extensions.json (also works in Windsurf)
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint"
  ],
  "unwantedRecommendations": [
    "github.copilot",          // conflicts with Supercomplete
    "tabnine.tabnine-vscode"   // conflicts with Supercomplete
  ]
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cascade modifies secrets | Sensitive files not excluded | Configure `.windsurfignore` |
| Untested AI code merged | No CI gate for tests | Require tests for new files |
| Conflicting AI suggestions | Multiple AI extensions | Disable competing extensions |
| Unreviewed bulk changes | Accept All without reading | Enforce per-file review policy |

## Examples

### Pre-Cascade Checklist
```bash
# Before starting Cascade task:
git status                    # clean working tree?
git checkout -b cascade/task  # new branch
git log --oneline -5          # know what's recent
```

## Resources
- [Windsurf Docs](https://docs.windsurf.com)
