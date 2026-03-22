---
name: coderabbit-common-errors
description: |
  Diagnose and fix CodeRabbit common errors and configuration issues.
  Use when CodeRabbit is not reviewing PRs, posting duplicate comments,
  ignoring configuration, or behaving unexpectedly.
  Trigger with phrases like "coderabbit error", "fix coderabbit",
  "coderabbit not working", "debug coderabbit", "coderabbit broken".
allowed-tools: Read, Grep, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, debugging, troubleshooting]

---
# CodeRabbit Common Errors

## Overview
Quick-reference troubleshooting guide for the most common CodeRabbit issues. CodeRabbit is a GitHub/GitLab App that reviews PRs automatically -- most problems are configuration issues, permission gaps, or YAML syntax errors rather than API failures.

## Prerequisites
- CodeRabbit GitHub App installed on repository
- Access to GitHub repository settings
- `.coderabbit.yaml` in repository root

## Instructions

### Step 1: Identify Your Issue Category

| Symptom | Category | Jump To |
|---------|----------|---------|
| No review posted on PR | Installation/Permissions | Error 1 |
| Review on some PRs but not others | Configuration | Error 2-4 |
| Too many comments / noise | Tuning | Error 5 |
| Config changes not taking effect | YAML Issues | Error 6 |
| Bot not responding to commands | Interaction | Error 7 |
| Review takes too long | Performance | Error 8 |

### Error 1: No Review Posted on PR
**Symptoms:** PR is open, targeting main, but no CodeRabbit review appears after 15+ minutes.

**Diagnosis:**
```bash
set -euo pipefail
# Check if CodeRabbit App is installed on this repo
gh api repos/OWNER/REPO/installation --jq '.app_slug' 2>/dev/null || echo "NOT INSTALLED"

# Check if the PR author has a CodeRabbit seat
# Go to app.coderabbit.ai > Organization > Seats
```

**Causes & Solutions:**
1. **App not installed**: Visit https://github.com/apps/coderabbitai and install on the repo
2. **Repo not selected**: In GitHub > Installed Apps > CodeRabbit, add the specific repository
3. **No seat assigned**: The PR author needs a CodeRabbit seat (app.coderabbit.ai > Subscription)
4. **Private repo without org plan**: Free tier only works on public repos

### Error 2: Reviews Only on Some Branches
**Symptoms:** Reviews appear on PRs to `main` but not `develop` or feature branches.

**Cause:** `base_branches` filter in configuration only includes specific branches.

**Fix:**
```yaml
# .coderabbit.yaml
reviews:
  auto_review:
    enabled: true
    base_branches:
      - main
      - develop
      - "release/*"     # Glob patterns work
      - "hotfix/*"
      # Remove base_branches entirely to review PRs to ALL branches
```

### Error 3: Reviews Skip Certain PRs
**Symptoms:** Some PRs get reviewed, others are silently skipped.

**Diagnosis checklist:**
```yaml
# Check these .coderabbit.yaml settings:
reviews:
  auto_review:
    drafts: false           # Draft PRs are skipped (expected behavior)
    ignore_title_keywords:  # PRs with these keywords in title are skipped
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"      # This skips dependency update PRs

# Also check: Is the PR author a bot?
# Bot PRs (dependabot, renovate) may not trigger reviews
# unless bot accounts have CodeRabbit seats
```

### Error 4: Reviews Include Generated/Unwanted Files
**Symptoms:** CodeRabbit comments on lock files, generated code, or build output.

**Fix:**
```yaml
# .coderabbit.yaml - Add path filters
reviews:
  path_filters:
    - "!**/*.lock"
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/*.snap"
    - "!**/generated/**"
    - "!dist/**"
    - "!**/*.min.js"
    - "!vendor/**"
    - "!**/*.generated.*"
```

### Error 5: Too Many Comments / Review Noise
**Symptoms:** CodeRabbit posts 10-20+ comments per PR, most are nitpicks.

**Fix:**
```yaml
# .coderabbit.yaml - Reduce comment volume
reviews:
  profile: "chill"           # Fewer comments, only significant issues
  # Options: chill (fewest) → assertive (balanced) → nitpicky (most)

  # Give context to prevent misguided comments
  path_instructions:
    - path: "src/legacy/**"
      instructions: |
        This is legacy code. Only flag security issues and bugs.
        Do NOT suggest refactoring or style changes.
    - path: "scripts/**"
      instructions: |
        One-off scripts. Do not enforce production standards.
        Only flag: security issues, destructive ops without confirmation.
```

### Error 6: Configuration Changes Not Taking Effect
**Symptoms:** You updated `.coderabbit.yaml` but reviews behave the same way.

**Diagnosis:**
```markdown
# In a PR comment, run:
@coderabbitai configuration

# CodeRabbit will reply with the active configuration as YAML.
# Compare with your .coderabbit.yaml to find discrepancies.

# Common causes:
# 1. YAML syntax error - entire config is ignored silently
# 2. Config not on the base branch - CodeRabbit reads config from the PR's base branch
# 3. Organization-level config overriding repo config
# 4. Wrong field name (e.g., "review_instructions" instead of "path_instructions")
```

**YAML validation:**
```bash
set -euo pipefail
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.coderabbit.yaml'))" && echo "YAML OK" || echo "YAML INVALID"

# Or use an online validator: https://www.yamllint.com/
```

### Error 7: Bot Not Responding to PR Comments
**Symptoms:** You post `@coderabbitai full review` but nothing happens.

**Causes & Solutions:**
1. **Typo in mention**: Must be exactly `@coderabbitai` (one word, lowercase)
2. **Comment in wrong location**: Commands work in PR comments, not commit comments
3. **Chat disabled**: Ensure `.coderabbit.yaml` has `chat: auto_reply: true`
4. **Rate limited**: Too many commands in quick succession; wait a few minutes

```yaml
# .coderabbit.yaml - Ensure chat is enabled
chat:
  auto_reply: true    # Required for @coderabbitai commands to work
```

### Error 8: Review Takes Too Long (15+ Minutes)
**Symptoms:** PR opened but CodeRabbit review not posted after 15 minutes.

**Causes:**
| PR Size | Expected Time | Action |
|---------|--------------|--------|
| < 200 lines | 2-3 min | Normal, wait |
| 200-500 lines | 3-7 min | Normal, wait |
| 500-1000 lines | 7-12 min | Consider splitting |
| 1000+ lines | 12-15+ min | Split PR or be patient |

**If it is been 20+ minutes on a small PR:**
```markdown
1. Check CodeRabbit status: https://status.coderabbit.ai
2. Try: @coderabbitai full review (force re-review)
3. Check GitHub App installation hasn't been suspended
4. Contact support via CodeRabbit Discord or email
```

### Step 2: Verify Fix
After applying a fix, create or update a PR and confirm CodeRabbit behaves as expected:
```bash
set -euo pipefail
# Force a re-review on an existing PR
gh pr comment PR_NUMBER --body "@coderabbitai full review"

# Or check the active config
gh pr comment PR_NUMBER --body "@coderabbitai configuration"
```

## Output
- Issue identified from symptom-based diagnosis
- Configuration fix applied to `.coderabbit.yaml`
- Fix verified via re-review or configuration check

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| All reviews stopped suddenly | GitHub App permissions revoked | Reinstall CodeRabbit GitHub App |
| "This repository is not configured" | Repo removed from App access | Re-add repo in GitHub App settings |
| YAML parse error in logs | Invalid `.coderabbit.yaml` | Validate YAML syntax before committing |
| Stale reviews on old PRs | PR was created before config change | Run `@coderabbitai full review` |

## Resources
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit FAQ](https://docs.coderabbit.ai/faq)
- [CodeRabbit Status Page](https://status.coderabbit.ai)
- [CodeRabbit Discord](https://discord.gg/coderabbit)

## Next Steps
For comprehensive debugging, see `coderabbit-debug-bundle`.
