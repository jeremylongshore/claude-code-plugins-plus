---
name: coderabbit-hello-world
description: |
  Create a minimal working CodeRabbit configuration and trigger your first AI review.
  Use when starting with CodeRabbit, testing your setup,
  or learning basic .coderabbit.yaml patterns.
  Trigger with phrases like "coderabbit hello world", "coderabbit example",
  "coderabbit quick start", "first coderabbit review".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, quickstart, testing]

---
# CodeRabbit Hello World

## Overview
Minimal working example demonstrating CodeRabbit AI code review. CodeRabbit reviews PRs automatically via a GitHub/GitLab App -- no SDK or API calls needed. You configure behavior through a `.coderabbit.yaml` file and interact via PR comments.

## Prerequisites
- CodeRabbit GitHub App installed (see `coderabbit-install-auth`)
- A repository with at least one branch

## Instructions

### Step 1: Create Minimal Configuration
```yaml
# .coderabbit.yaml (repository root)
language: "en-US"
reviews:
  profile: "assertive"
  high_level_summary: true
  auto_review:
    enabled: true
    drafts: false
chat:
  auto_reply: true
```

### Step 2: Add Path-Specific Instructions
```yaml
# .coderabbit.yaml - add review context for better feedback
reviews:
  profile: "assertive"
  high_level_summary: true
  auto_review:
    enabled: true
    drafts: false
  path_instructions:
    - path: "src/**/*.ts"
      instructions: "Check for proper TypeScript types. Flag any use of `any`."
    - path: "**/*.test.*"
      instructions: "Verify edge cases are covered. Check async handling."
chat:
  auto_reply: true
```

### Step 3: Create a PR to Trigger Review
```bash
set -euo pipefail
git checkout -b feat/hello-coderabbit

# Add the configuration file
cat > .coderabbit.yaml << 'YAML'
language: "en-US"
reviews:
  profile: "assertive"
  high_level_summary: true
  auto_review:
    enabled: true
    drafts: false
  path_instructions:
    - path: "src/**"
      instructions: "Check for proper error handling and input validation."
chat:
  auto_reply: true
YAML

git add .coderabbit.yaml
git commit -m "feat: add CodeRabbit AI code review configuration"
git push -u origin feat/hello-coderabbit
gh pr create --title "feat: enable CodeRabbit AI code review" \
  --body "Adding .coderabbit.yaml for automated code reviews"
```

### Step 4: Interact with CodeRabbit on the PR
Once CodeRabbit posts its review (typically 2-5 minutes), you can interact:
```markdown
# In a PR comment, use these commands:
@coderabbitai summary        # Get a walkthrough of all changes
@coderabbitai full review    # Re-run a complete review from scratch
@coderabbitai resolve        # Mark all CodeRabbit comments as resolved
@coderabbitai help           # List all available commands

# Reply to any CodeRabbit comment to have a conversation about the feedback
# CodeRabbit will respond with context-aware explanations
```

### Step 5: Try the CLI for Local Reviews (Optional)
```bash
set -euo pipefail
# Review staged changes before committing
git add -A
cr review

# Review with interactive mode for back-and-forth discussion
cr review --interactive

# Review specific files
cr review src/index.ts src/utils.ts
```

## What CodeRabbit Posts on Your PR
1. **Walkthrough comment**: High-level summary of all changes with a file-by-file breakdown
2. **Sequence diagram**: Visual control flow of the changes (if enabled)
3. **Line-level comments**: Specific suggestions on individual code lines
4. **Review status**: Approved or changes-requested based on severity of findings

## Output
- `.coderabbit.yaml` committed to repository root
- First AI review posted on a test PR within 2-5 minutes
- Interactive review conversation demonstrated

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No review appears | App not installed on this repo | Check GitHub App > Repository access |
| YAML syntax error | Invalid configuration | Validate YAML at yamlchecker.com |
| Review on wrong branch | Missing base_branches filter | Add `base_branches: [main]` to config |
| Bot not responding to commands | Typo in mention | Must use exact `@coderabbitai` mention |

## Resources
- [YAML Configuration Guide](https://docs.coderabbit.ai/getting-started/yaml-configuration)
- [Review Commands Reference](https://docs.coderabbit.ai/reference/review-commands)
- [CodeRabbit CLI](https://www.coderabbit.ai/cli)

## Next Steps
Proceed to `coderabbit-local-dev-loop` for a full development workflow with CodeRabbit.
