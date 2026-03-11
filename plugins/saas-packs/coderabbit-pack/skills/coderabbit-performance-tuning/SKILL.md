---
name: coderabbit-performance-tuning
description: |
  Optimize CodeRabbit API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for CodeRabbit integrations.
  Trigger with phrases like "coderabbit performance", "optimize coderabbit",
  "coderabbit latency", "coderabbit caching", "coderabbit slow", "coderabbit batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# CodeRabbit Performance Tuning

## Overview
Optimize CodeRabbit review speed, relevance, and developer workflow integration. CodeRabbit reviews typically take 2-10 minutes depending on PR size, with large PRs (1000+ lines) taking up to 15 minutes. The main performance levers are: keeping PRs small (smaller diffs = faster, more relevant reviews), configuring path-specific instructions (reduces noise, increases signal), and using incremental reviews (only review changed files on push, not the full PR again).

## Prerequisites
- CodeRabbit installed on GitHub/GitLab organization
- `.coderabbit.yaml` configuration file in repositories
- Understanding of review patterns and team feedback

## Instructions

### Step 1: Keep PRs Small for Faster Reviews
```yaml
# PR size directly impacts review speed and quality
size_guidelines:
  small:    # <200 lines changed
    review_time: "2-3 minutes"
    quality: "High - focused, actionable comments"
  medium:   # 200-500 lines
    review_time: "3-7 minutes"
    quality: "Good - may miss nuanced issues"
  large:    # 500-1000 lines
    review_time: "7-12 minutes"
    quality: "Moderate - broad strokes only"
  huge:     # 1000+ lines
    review_time: "12-15+ minutes"
    quality: "Low - too much context to process well"

# Best practice: enforce PR size limits with CI checks
# max_lines_changed: 500
```

### Step 2: Use Path-Specific Instructions for Relevance
```yaml
# .coderabbit.yaml - Give context so reviews are actionable
reviews:
  path_instructions:
    - path: "src/api/**"
      instructions: |
        Check for: proper error handling, input validation, auth middleware.
        Ignore: logging format, import order.
    - path: "src/components/**"
      instructions: |
        Check for: accessibility (aria labels), performance (no inline styles).
        Ignore: CSS naming conventions (handled by linter).
    - path: "tests/**"
      instructions: |
        Check for: assertion completeness, edge cases.
        Ignore: test structure (handled by testing framework conventions).
```

### Step 3: Configure Incremental Reviews
```yaml
# .coderabbit.yaml - Only re-review changed files on push
reviews:
  auto_review:
    enabled: true
    incremental: true    # Re-review only changed files on new pushes
    drafts: false        # Skip draft PRs (work in progress)
    base_branches: [main, develop]  # Only PRs targeting these branches
```

### Step 4: Reduce Noise with Smart Exclusions
```yaml
# .coderabbit.yaml - Skip files that don't benefit from AI review
reviews:
  auto_review:
    ignore_paths:
      - "**/*.lock"             # Package lock files
      - "**/*.snap"             # Test snapshots
      - "**/*.generated.*"      # Generated code
      - "**/*.min.js"           # Minified files
      - "**/vendor/**"          # Third-party code
      - "**/__mocks__/**"       # Test mocks
      - "**/fixtures/**"        # Test fixtures
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"
```

### Step 5: Tune Review Profile for Your Team
```yaml
# Match review aggressiveness to team preferences
profiles:
  chill:       # Few comments, only major issues
    best_for: "Senior teams, high-trust environments"
    comment_count: "1-3 per PR"

  assertive:   # Balanced signal-to-noise
    best_for: "Most teams (recommended default)"
    comment_count: "3-8 per PR"

  nitpicky:    # Detailed comments on style and best practices
    best_for: "Junior teams, onboarding, compliance-critical"
    comment_count: "8-15 per PR"
    warning: "May cause review fatigue if team isn't expecting it"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review takes 15+ minutes | PR too large (1000+ lines) | Split into smaller PRs |
| Too many irrelevant comments | No path_instructions configured | Add context-specific instructions |
| Reviews on generated files | No ignore_paths configured | Add generated file patterns to exclusions |
| Team ignoring reviews | Profile too nitpicky | Switch to `assertive` or `chill` profile |

## Examples
```yaml
# Optimized .coderabbit.yaml for a typical backend service
reviews:
  profile: "assertive"
  auto_review:
    enabled: true
    incremental: true
    drafts: false
    base_branches: [main]
    ignore_paths: ["**/*.lock", "**/*.snap", "**/vendor/**", "dist/**"]
  path_instructions:
    - path: "src/auth/**"
      instructions: "Security-critical. Check for auth bypass and injection."
```
