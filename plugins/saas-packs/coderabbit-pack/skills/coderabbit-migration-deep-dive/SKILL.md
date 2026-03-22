---
name: coderabbit-migration-deep-dive
description: |
  Migrate to CodeRabbit from other code review tools or roll out across a large organization.
  Use when switching from another AI review tool, migrating from manual-only reviews,
  or planning a phased CodeRabbit adoption strategy.
  Trigger with phrases like "migrate to coderabbit", "coderabbit migration",
  "switch to coderabbit", "coderabbit from reviewbot", "adopt coderabbit", "replace code review tool".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, migration, adoption]

---
# CodeRabbit Migration Deep Dive

## Overview
Comprehensive guide for migrating to CodeRabbit from other AI code review tools (Codacy, SonarCloud, DeepSource, Sourcery) or from manual-only code review. Covers assessment, phased rollout, configuration transfer, team buy-in, and measuring success.

## Prerequisites
- GitHub/GitLab organization admin access
- Inventory of current review tools and their configurations
- Understanding of team review workflows
- Budget approval for CodeRabbit seats

## Migration Types

| From | Complexity | Duration | Key Challenge |
|------|-----------|----------|---------------|
| Manual-only reviews | Low | 1-2 weeks | Team adoption |
| Codacy / SonarCloud | Medium | 2-3 weeks | Rule translation |
| DeepSource / Sourcery | Medium | 2-3 weeks | Config migration |
| Custom review bots | High | 3-4 weeks | Workflow redesign |
| Multiple tools | High | 4-6 weeks | Consolidation |

## Instructions

### Step 1: Assess Current State
```bash
set -euo pipefail
ORG="${1:-your-org}"

echo "=== Code Review Tool Assessment ==="

# Check for existing review tools
echo "--- Installed GitHub Apps ---"
gh api "orgs/$ORG/installations" --jq '.installations[] | "\(.app_slug) (ID: \(.id))"' 2>/dev/null

echo ""
echo "--- Review Tool Config Files ---"
for REPO in $(gh repo list "$ORG" --limit 20 --json name --jq '.[].name'); do
  # Check for common review tool configs
  for CONFIG in ".codacy.yml" "sonar-project.properties" ".deepsource.toml" ".sourcery.yaml" ".coderabbit.yaml"; do
    EXISTS=$(gh api "repos/$ORG/$REPO/contents/$CONFIG" --jq '.name' 2>/dev/null || echo "")
    if [ -n "$EXISTS" ]; then
      echo "  $REPO: $CONFIG"
    fi
  done
done
```

### Step 2: Map Review Rules to CodeRabbit Path Instructions
```yaml
# Common rule translations:

# Codacy / SonarCloud "code smells" → CodeRabbit path_instructions
# Before (Codacy):
#   rules:
#     - id: "javascript/complexity"
#     - id: "javascript/error-handling"
#
# After (CodeRabbit):
reviews:
  path_instructions:
    - path: "src/**/*.ts"
      instructions: |
        Check for:
        - Functions with cyclomatic complexity > 10 (suggest refactoring)
        - Missing error handling in async operations
        - Empty catch blocks
        - Unused variables and imports

# DeepSource "analyzer" → CodeRabbit path_instructions
# Before (DeepSource):
#   analyzers:
#     - name: javascript
#       enabled: true
#       meta:
#         plugins: [react]
#
# After (CodeRabbit):
    - path: "src/components/**"
      instructions: |
        React-specific checks:
        - No conditional hooks
        - Proper cleanup in useEffect
        - Memoization for expensive computations
        - Accessibility (aria labels, keyboard navigation)

# Sourcery "refactoring" → CodeRabbit path_instructions
# Before (Sourcery):
#   refactor:
#     skip: [dont-import-test-modules]
#
# After (CodeRabbit):
    - path: "**/*.py"
      instructions: |
        Python best practices:
        - Suggest list comprehensions over manual loops where appropriate
        - Flag mutable default arguments
        - Check for proper context manager usage
```

### Step 3: Phase 1 -- Parallel Run (Week 1-2)
```yaml
# Run CodeRabbit alongside existing tool for comparison
# .coderabbit.yaml - Start with non-blocking mode
reviews:
  profile: "chill"                    # Fewer comments during evaluation
  request_changes_workflow: false     # Don't block merges
  high_level_summary: true            # Show walkthrough for evaluation

  auto_review:
    enabled: true
    drafts: false
    base_branches: [main, develop]

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!dist/**"
    - "!vendor/**"

chat:
  auto_reply: true
```

```markdown
# During parallel run, track:
1. Comment quality: Are CodeRabbit comments actionable?
2. Coverage: Does it catch what the old tool catches?
3. Speed: Is review posted before human reviewers start?
4. Noise: Are there many false positives?
5. Team reaction: Do developers find it helpful?
```

### Step 4: Phase 2 -- Primary Tool (Week 3-4)
```yaml
# After successful parallel run, make CodeRabbit primary
# .coderabbit.yaml - Enable full features
reviews:
  profile: "assertive"                # Balanced feedback
  request_changes_workflow: true      # Now blocking
  high_level_summary: true
  sequence_diagrams: true

  auto_review:
    enabled: true
    drafts: false
    base_branches: [main, develop]

  path_instructions:
    # Transfer your best rules from the old tool
    - path: "src/api/**"
      instructions: |
        Review for: input validation, proper HTTP status codes,
        auth middleware usage, error response format.
    - path: "src/db/**"
      instructions: |
        Review for: parameterized queries, transaction boundaries,
        connection cleanup, index usage. Flag N+1 patterns.
    - path: "**/*.test.*"
      instructions: |
        Review for: assertion completeness, edge cases, async handling.
        Do NOT comment on test naming or import order.

  # Keep exclusions from old tool
  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!**/generated/**"
    - "!dist/**"
    - "!vendor/**"
```

### Step 5: Phase 3 -- Decommission Old Tool (Week 4-6)
```bash
set -euo pipefail
ORG="${1:-your-org}"

echo "=== Old Tool Decommission Checklist ==="

# 1. Remove old tool config files
echo "--- Config Files to Remove ---"
for REPO in $(gh repo list "$ORG" --limit 50 --json name --jq '.[].name'); do
  for CONFIG in ".codacy.yml" "sonar-project.properties" ".deepsource.toml" ".sourcery.yaml"; do
    EXISTS=$(gh api "repos/$ORG/$REPO/contents/$CONFIG" --jq '.name' 2>/dev/null || echo "")
    if [ -n "$EXISTS" ]; then
      echo "  rm $REPO/$CONFIG"
    fi
  done
done

echo ""
echo "--- Steps ---"
echo "1. Remove old tool GitHub App from org settings"
echo "2. Delete old tool config files from repos"
echo "3. Update branch protection rules (replace old check with coderabbitai)"
echo "4. Cancel old tool subscription"
echo "5. Update team documentation and onboarding guides"
```

### Step 6: Measure Migration Success
```bash
set -euo pipefail
ORG="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== CodeRabbit Adoption Metrics ==="

# Review coverage
TOTAL=0
REVIEWED=0
for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=30" --jq '.[].number'); do
  TOTAL=$((TOTAL + 1))
  CR=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  [ "$CR" -gt 0 ] && REVIEWED=$((REVIEWED + 1))
done

echo "Review coverage: $REVIEWED/$TOTAL PRs ($(( REVIEWED * 100 / (TOTAL > 0 ? TOTAL : 1) ))%)"
echo ""
echo "Target metrics:"
echo "  - Coverage > 90%: CodeRabbit reviewing most PRs"
echo "  - Time-to-review < 5 min: Fast feedback loop"
echo "  - Team satisfaction: Survey developers after 2 weeks"
```

## Output
- Current review tool assessment completed
- Rule translation from old tool to CodeRabbit path_instructions
- Phased migration plan executed
- Old tool decommissioned
- Adoption metrics measured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Old tool conflicts with CodeRabbit | Both posting reviews | Run parallel briefly, then disable old tool |
| Rules don't translate 1:1 | Different analysis approaches | Focus on intent, not exact rule matching |
| Team prefers old tool | Familiarity bias | Run parallel for 2 weeks, compare results |
| Branch protection breaks | Old check name removed | Update to `coderabbitai` check name |
| Higher seat cost than old tool | Per-seat vs per-repo pricing | Scope repos to reduce seat count |

## Resources
- [CodeRabbit vs Alternatives](https://coderabbit.ai/compare)
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [Migration from Codacy](https://docs.coderabbit.ai/guides/migration)
- [CodeRabbit Path Instructions](https://docs.coderabbit.ai/guides/review-instructions)

## Next Steps
For ongoing configuration tuning, see `coderabbit-core-workflow-b`.
