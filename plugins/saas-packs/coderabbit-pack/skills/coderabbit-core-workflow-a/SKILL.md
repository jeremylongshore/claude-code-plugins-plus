---
name: coderabbit-core-workflow-a
description: |
  Execute CodeRabbit primary workflow: automated PR code review with configuration.
  Use when setting up automated code reviews on pull requests,
  configuring review behavior, or establishing the core CodeRabbit review loop.
  Trigger with phrases like "coderabbit review workflow", "coderabbit PR review",
  "coderabbit auto review", "configure coderabbit reviews".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, workflow, code-review]

---
# CodeRabbit Core Workflow A: Automated PR Review

## Overview
The primary CodeRabbit workflow: a developer opens a PR, CodeRabbit automatically analyzes the diff, posts a walkthrough summary and line-level comments, and the developer addresses feedback. This skill covers configuration, review profiles, path instructions, and the full review lifecycle.

## Prerequisites
- CodeRabbit GitHub App installed (see `coderabbit-install-auth`)
- `.coderabbit.yaml` in repository root
- At least one PR-capable branch

## Instructions

### Step 1: Configure the Review Pipeline
```yaml
# .coderabbit.yaml - Production-ready configuration
language: "en-US"
early_access: false

reviews:
  profile: "assertive"              # chill = less feedback, assertive = more thorough
  request_changes_workflow: true    # CodeRabbit marks review as "changes requested" for issues
  high_level_summary: true          # Post a walkthrough comment summarizing all changes
  high_level_summary_in_walkthrough: true
  review_status: true               # Show review progress status
  collapse_walkthrough: false       # Keep walkthrough expanded
  sequence_diagrams: true           # Generate control flow diagrams
  poem: false                       # Disable poems in review summary

  auto_review:
    enabled: true
    drafts: false                   # Skip draft PRs
    base_branches:
      - main
      - develop
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!**/generated/**"
    - "!dist/**"
    - "!**/*.min.js"
    - "!vendor/**"

  path_instructions:
    - path: "src/api/**"
      instructions: |
        Review for: input validation, proper HTTP status codes, auth middleware usage,
        error response format per RFC 7807. Flag missing error handling.
    - path: "src/db/**"
      instructions: |
        Review for: parameterized queries (no string concatenation), transaction boundaries,
        proper connection cleanup, index usage. Flag N+1 query patterns.
    - path: "**/*.test.*"
      instructions: |
        Review for: assertion completeness, edge case coverage, proper async handling.
        Do NOT comment on test naming conventions or import order.
    - path: ".github/workflows/**"
      instructions: |
        Review for: pinned action versions (use SHA not tag), no secrets in logs,
        timeout-minutes on all jobs, OIDC for cloud auth.

chat:
  auto_reply: true

# Finishing touches configuration
reviews:
  finishing_touches:
    docstrings:
      enabled: true       # Allow @coderabbitai generate-docstrings command
```

### Step 2: Understand the Review Lifecycle
```
Developer opens/updates PR
         │
         ▼
┌─────────────────────────────────┐
│ CodeRabbit analyzes diff        │
│ (typically 2-5 min, up to 15   │
│  min for 1000+ line PRs)       │
└─────────┬───────────────────────┘
          │
          ├──▶ Walkthrough comment (summary + sequence diagram)
          │
          ├──▶ Line-level comments (bugs, suggestions, improvements)
          │
          └──▶ Review state (approved / changes_requested)
                    │
                    ▼
         Developer addresses feedback
                    │
          ┌─────────┴──────────┐
          │                    │
    Reply to comment     Push new commits
    (conversation)       (incremental re-review)
          │                    │
          ▼                    ▼
    CodeRabbit responds  CodeRabbit reviews
    with explanation     only changed files
```

### Step 3: Interact with Reviews
```markdown
# In any PR comment:
@coderabbitai full review          # Re-review all files from scratch
@coderabbitai summary              # Regenerate walkthrough summary
@coderabbitai resolve              # Mark all CodeRabbit comments as resolved
@coderabbitai generate-docstrings  # Auto-generate docstrings for functions
@coderabbitai configuration        # Show current active config as YAML
@coderabbitai help                 # List all commands

# Reply to any CodeRabbit inline comment to discuss the feedback.
# CodeRabbit maintains conversation context and will explain its reasoning.

# In PR description, add instructions for this specific review:
# "Focus on security implications of the auth changes"
```

### Step 4: Configure Finishing Touch Recipes
```yaml
# .coderabbit.yaml - Custom finishing touch recipes (open beta)
finishing_touches:
  recipes:
    - name: "fix-imports"
      description: "Sort and organize imports"
      instructions: |
        Sort all imports alphabetically. Group: external packages first,
        then internal modules, then relative imports. Remove unused imports.

    - name: "tighten-types"
      description: "Replace any with specific types"
      instructions: |
        Replace all `any` types with proper TypeScript types.
        Use `unknown` for truly unknown values. Add type guards where needed.
```

```markdown
# Trigger recipes in a PR comment:
@coderabbitai run fix-imports
@coderabbitai run tighten-types

# Or check the boxes in the Finishing Touches section of the walkthrough
```

## Output
- Automated review on every PR targeting configured branches
- Walkthrough summary with sequence diagrams
- Line-level feedback categorized by severity
- Interactive conversation on review comments
- Finishing touch recipes for automated code improvements

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review takes 15+ minutes | PR has 1000+ changed lines | Split into smaller PRs |
| No review posted | PR targets non-configured branch | Add branch to `base_branches` |
| Reviews on generated files | Missing path_filters | Add `!**/generated/**` to path_filters |
| Too many nitpick comments | Profile set to assertive | Switch to `chill` for experienced teams |
| Config changes not applied | YAML syntax error | Run `@coderabbitai configuration` to verify |
| Review on draft PR | `drafts: true` in config | Set `drafts: false` to skip drafts |

## Resources
- [Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [Review Commands](https://docs.coderabbit.ai/reference/review-commands)
- [Finishing Touches](https://docs.coderabbit.ai/finishing-touches/index)

## Next Steps
For configuration tuning and noise reduction, see `coderabbit-core-workflow-b`.
