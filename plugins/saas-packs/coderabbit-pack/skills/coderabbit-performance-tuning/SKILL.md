---
name: coderabbit-performance-tuning
description: |
  Optimize CodeRabbit review speed, relevance, and signal-to-noise ratio.
  Use when reviews take too long, contain too many irrelevant comments,
  or when teams are experiencing review fatigue.
  Trigger with phrases like "coderabbit performance", "optimize coderabbit",
  "coderabbit slow", "coderabbit noise", "coderabbit too many comments", "coderabbit relevance".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, performance, tuning]

---
# CodeRabbit Performance Tuning

## Overview
Optimize CodeRabbit review speed, relevance, and developer experience. Review time is primarily a function of PR size. Comment quality is controlled by profile selection, path instructions, and learnings. This skill covers all the levers for tuning CodeRabbit to your team's needs.

## Prerequisites
- CodeRabbit installed and producing reviews
- `.coderabbit.yaml` in repository root
- Several PRs worth of review history to evaluate

## Performance Factors

| Factor | Impact | You Control? |
|--------|--------|-------------|
| PR size (lines changed) | Review speed (2-15 min) | Yes -- keep PRs small |
| Profile (chill/assertive) | Comment volume | Yes -- `.coderabbit.yaml` |
| Path instructions | Comment relevance | Yes -- `.coderabbit.yaml` |
| Path filters | Files reviewed | Yes -- `.coderabbit.yaml` |
| Learnings | Long-term quality | Yes -- via PR comment feedback |
| CodeRabbit service load | Review latency | No -- check status page |

## Instructions

### Step 1: Optimize PR Size for Faster Reviews
```markdown
# PR size directly impacts review speed and quality

| PR Size | Review Time | Review Quality |
|---------|------------|----------------|
| < 200 lines | 2-3 min | Excellent -- focused, actionable |
| 200-500 lines | 3-7 min | Good -- catches most issues |
| 500-1000 lines | 7-12 min | Moderate -- may miss nuanced issues |
| 1000+ lines | 12-15+ min | Low -- too much context |

# Enforce PR size limits with CI:
```

```yaml
# .github/workflows/pr-size.yml
name: PR Size Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check PR size
        run: |
          TOTAL=$(git diff --stat origin/${{ github.base_ref }}...HEAD | tail -1 | \
            grep -oP '\d+ insertion|d+ deletion' | grep -oP '\d+' | \
            awk '{sum+=$1} END {print sum+0}')
          echo "Lines changed: $TOTAL"
          if [ "$TOTAL" -gt 500 ]; then
            echo "::warning::Large PR ($TOTAL lines). Consider splitting for better CodeRabbit review quality."
          fi
```

### Step 2: Choose the Right Review Profile
```yaml
# .coderabbit.yaml - Profile comparison
reviews:
  profile: "assertive"    # Start here, tune based on team feedback

# Profile decision guide:
#
# "chill":
#   - 1-3 comments per PR
#   - Only critical issues and bugs
#   - Best for: senior teams, high-trust environments
#   - Warning: may miss moderate issues
#
# "assertive" (recommended):
#   - 3-8 comments per PR
#   - Bugs, security, best practices
#   - Best for: most teams
#   - Good balance of signal-to-noise
#
# Tune based on metrics:
#   - Team ignoring most comments? → Switch to chill
#   - Security issues slipping through? → Stay on assertive
#   - New or junior team? → assertive catches more learning opportunities
```

### Step 3: Add Path Instructions for Relevance
```yaml
# .coderabbit.yaml - Context makes reviews more relevant
reviews:
  path_instructions:
    # Tell CodeRabbit WHAT to look for (increases relevance)
    - path: "src/api/**"
      instructions: |
        Review for: input validation, proper HTTP status codes, auth middleware.
        Ignore: import order, logging format.

    - path: "src/components/**"
      instructions: |
        Review for: accessibility (aria labels), performance (memo/useMemo).
        Ignore: CSS naming, component file structure.

    - path: "**/*.test.*"
      instructions: |
        Review for: assertion completeness, edge cases, async handling.
        Do NOT comment on: test naming conventions, import order.

    # Tell CodeRabbit what NOT to comment on (reduces noise)
    - path: "src/legacy/**"
      instructions: |
        Legacy code being incrementally migrated.
        ONLY flag: security vulnerabilities, data loss risks, crashes.
        Do NOT suggest: refactoring, naming changes, style improvements.

    - path: "scripts/**"
      instructions: |
        One-off scripts. Only flag: security issues, destructive operations
        without confirmation, missing error handling on file/network ops.
```

### Step 4: Exclude Low-Value Files
```yaml
# .coderabbit.yaml - Skip files that generate noise
reviews:
  path_filters:
    # Auto-generated files (no useful feedback possible)
    - "!**/*.lock"
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/*.generated.*"
    - "!**/generated/**"

    # Build output
    - "!dist/**"
    - "!build/**"
    - "!**/*.min.js"
    - "!**/*.min.css"

    # Test fixtures and snapshots
    - "!**/*.snap"
    - "!**/__mocks__/**"
    - "!**/fixtures/**"
    - "!**/testdata/**"

    # Third-party code
    - "!vendor/**"
    - "!node_modules/**"

    # Data files
    - "!**/*.csv"
    - "!**/*.sql"           # DB migrations (review manually)

  auto_review:
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"
      - "chore(deps)"
      - "auto-generated"
    drafts: false            # Skip draft PRs
```

### Step 5: Train CodeRabbit with Learnings
```markdown
# CodeRabbit learns from your feedback on PR comments.
# This improves relevance over time.

# When CodeRabbit gives feedback you disagree with, reply:
"We intentionally use default exports in this project for Next.js pages.
Please don't flag default exports in files under src/pages/."

# When CodeRabbit catches something valuable, reinforce it:
"Good catch! Always flag missing error boundaries in React components."

# View and manage learnings:
# app.coderabbit.ai > Organization > Learnings

# Learnings persist across PRs and repos within the organization.
# They are the most effective long-term tuning mechanism.
```

### Step 6: Measure Improvement
```bash
set -euo pipefail
ORG="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== Review Quality Metrics ==="

TOTAL_PRS=0
TOTAL_COMMENTS=0

for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=20" --jq '.[].number'); do
  COMMENTS=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/comments" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  if [ "$COMMENTS" -gt 0 ]; then
    TOTAL_PRS=$((TOTAL_PRS + 1))
    TOTAL_COMMENTS=$((TOTAL_COMMENTS + COMMENTS))
    echo "PR #$PR_NUM: $COMMENTS comments"
  fi
done

if [ "$TOTAL_PRS" -gt 0 ]; then
  AVG=$(( TOTAL_COMMENTS / TOTAL_PRS ))
  echo ""
  echo "Average: $AVG comments/PR"
  echo ""
  if [ "$AVG" -gt 10 ]; then
    echo "Recommendation: Switch to 'chill' profile or add path_instructions"
  elif [ "$AVG" -lt 2 ]; then
    echo "Recommendation: Switch to 'assertive' profile for more thorough reviews"
  else
    echo "Good signal-to-noise ratio"
  fi
fi
```

## Output
- PR size guidelines documented and enforced via CI
- Review profile selected based on team needs
- Path instructions configured for relevant feedback
- Low-value files excluded from review
- Learnings trained from team feedback
- Review quality measured with metrics

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review takes 15+ min | PR too large (1000+ lines) | Split into smaller PRs |
| Too many irrelevant comments | No path_instructions | Add context for key directories |
| Team ignoring reviews | Review fatigue from noise | Switch to `chill`, add exclusions |
| Same issue flagged repeatedly | Learning not created | Reply to comment stating the preference |
| Reviews on generated code | Missing path_filters | Add `!**/generated/**` to exclusions |

## Resources
- [CodeRabbit Review Profiles](https://docs.coderabbit.ai/reference/configuration)
- [Path Instructions Guide](https://docs.coderabbit.ai/guides/review-instructions)
- [CodeRabbit Learnings](https://docs.coderabbit.ai/guides/learnings)

## Next Steps
For learnings and advanced tuning, see `coderabbit-core-workflow-b`.
