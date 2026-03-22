---
name: coderabbit-prod-checklist
description: |
  Execute CodeRabbit production readiness checklist for org-wide deployment.
  Use when preparing to enforce CodeRabbit reviews, going live with required checks,
  or auditing CodeRabbit configuration before making it a merge gate.
  Trigger with phrases like "coderabbit production", "coderabbit go-live",
  "coderabbit launch checklist", "coderabbit readiness", "coderabbit pre-launch".
allowed-tools: Read, Bash(gh:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, deployment, production, checklist]

---
# CodeRabbit Production Checklist

## Overview
Complete checklist for deploying CodeRabbit as a production merge gate. Covers the transition from "optional AI review" to "required status check that blocks merges." Ensures configuration is tuned, team is onboarded, and fallback procedures are documented.

## Prerequisites
- CodeRabbit installed and running in non-blocking mode for 1-2 weeks
- Team has seen CodeRabbit reviews and provided feedback
- `.coderabbit.yaml` tuned based on pilot feedback
- GitHub organization admin access

## Instructions

### Step 1: Pre-Launch Configuration Audit
```markdown
# Run through each item before going live:

## App Installation
- [ ] CodeRabbit GitHub App installed on all target repos
- [ ] Repository access scoped correctly (all repos vs select)
- [ ] Seat assignment policy set (active committers vs manual)
- [ ] Bot accounts excluded from seats (dependabot, renovate)

## Configuration
- [ ] `.coderabbit.yaml` committed to main branch
- [ ] YAML syntax validated (no parse errors)
- [ ] `auto_review.enabled: true`
- [ ] `auto_review.drafts: false` (skip draft PRs)
- [ ] `base_branches` includes all target branches (main, develop)
- [ ] `path_filters` excludes generated/lock/vendor files
- [ ] `path_instructions` configured for key directories
- [ ] `chat.auto_reply: true`

## Review Behavior
- [ ] Profile set to "assertive" (or team's preferred level)
- [ ] `request_changes_workflow` decision documented:
  - `true`: CodeRabbit blocks merge when issues found
  - `false`: CodeRabbit only comments (non-blocking)
- [ ] Org-level defaults in `.github/.coderabbit.yaml` if multi-repo
```

### Step 2: Validate Configuration
```bash
set -euo pipefail
echo "=== CodeRabbit Production Readiness Check ==="

# 1. YAML syntax
echo "--- Config Validation ---"
if [ -f .coderabbit.yaml ]; then
  python3 -c "
import yaml, sys
try:
    config = yaml.safe_load(open('.coderabbit.yaml'))
    print('YAML syntax: PASS')

    reviews = config.get('reviews', {})
    auto = reviews.get('auto_review', {})

    checks = {
        'auto_review.enabled': auto.get('enabled', False) == True,
        'auto_review.drafts': auto.get('drafts', True) == False,
        'path_filters configured': len(reviews.get('path_filters', [])) > 0,
        'path_instructions configured': len(reviews.get('path_instructions', [])) > 0,
        'chat.auto_reply': config.get('chat', {}).get('auto_reply', False) == True,
    }

    for name, passed in checks.items():
        status = 'PASS' if passed else 'WARN'
        print(f'  {name}: {status}')

    if all(checks.values()):
        print('Overall: READY FOR PRODUCTION')
    else:
        print('Overall: Review warnings above before going live')

except yaml.YAMLError as e:
    print(f'YAML syntax: FAIL ({e})')
    sys.exit(1)
" 2>&1
else
  echo "FAIL: .coderabbit.yaml not found"
fi
```

### Step 3: Verify Review History
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo ""
echo "--- Review History Check ---"
REVIEWED=0
TOTAL=0

for PR_NUM in $(gh api "repos/$OWNER/$REPO/pulls?state=all&per_page=20" --jq '.[].number'); do
  TOTAL=$((TOTAL + 1))
  CR=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  [ "$CR" -gt 0 ] && REVIEWED=$((REVIEWED + 1))
done

echo "Coverage: $REVIEWED/$TOTAL PRs reviewed by CodeRabbit"
if [ "$TOTAL" -gt 0 ] && [ "$((REVIEWED * 100 / TOTAL))" -lt 80 ]; then
  echo "WARNING: Coverage below 80%. Check base_branches and ignore_title_keywords."
else
  echo "Coverage: PASS"
fi
```

### Step 4: Team Readiness Checklist
```markdown
## Team Onboarding
- [ ] Team briefed on CodeRabbit (what it does, how to interact)
- [ ] Quick reference shared:
  - `@coderabbitai full review` — re-review from scratch
  - `@coderabbitai summary` — regenerate walkthrough
  - `@coderabbitai resolve` — mark all comments resolved
  - `@coderabbitai help` — list all commands
- [ ] Team knows to reply to comments to train learnings
- [ ] "WIP" in PR title skips review (documented)
- [ ] Escalation path defined for false positives

## Fallback Procedures
- [ ] Admin merge bypass documented (for emergencies)
- [ ] Process for temporarily disabling CodeRabbit:
  1. Remove from branch protection required checks
  2. Set `auto_review.enabled: false` in config
  3. Or uninstall the GitHub App from the repo
- [ ] Contact info for CodeRabbit support documented
```

### Step 5: Enable as Required Check
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo ""
echo "--- Enabling CodeRabbit as Required Check ---"

# Update branch protection to require CodeRabbit
gh api "repos/$OWNER/$REPO/branches/main/protection" \
  --method PUT \
  --field 'required_status_checks={"strict":true,"contexts":["coderabbitai"]}' \
  --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
  --field 'enforce_admins=false' \
  --field 'restrictions=null'

echo "DONE: CodeRabbit is now a required check on $OWNER/$REPO main branch"
echo ""
echo "To revert (emergency):"
echo "  gh api repos/$OWNER/$REPO/branches/main/protection --method DELETE"
```

### Step 6: Update .coderabbit.yaml for Production
```yaml
# .coderabbit.yaml - Production configuration
language: "en-US"
early_access: false

reviews:
  profile: "assertive"
  request_changes_workflow: true      # NOW blocking (was false during pilot)
  high_level_summary: true
  high_level_summary_in_walkthrough: true
  review_status: true
  collapse_walkthrough: false
  sequence_diagrams: true
  poem: false

  auto_review:
    enabled: true
    drafts: false
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
    - "!vendor/**"

  path_instructions:
    - path: "src/api/**"
      instructions: "Review for input validation, auth middleware, error handling."
    - path: "src/db/**"
      instructions: "Review for parameterized queries, transactions, N+1 patterns."
    - path: "**/*.test.*"
      instructions: "Review for edge cases and assertion completeness. Skip style."

chat:
  auto_reply: true
```

### Step 7: Post-Launch Monitoring
```markdown
# First 48 hours after go-live:

## Monitor:
- [ ] All PRs to main are getting CodeRabbit reviews
- [ ] No PRs blocked by CodeRabbit timeout (> 15 min)
- [ ] Team is not overwhelmed by review volume
- [ ] No legitimate emergency PRs blocked

## Week 1 review:
- [ ] Review coverage > 90%
- [ ] No team complaints about false positives
- [ ] Learnings being created from feedback
- [ ] Emergency bypass has not been needed (or was used correctly)
```

## Output
- Configuration audited and validated
- Review history confirms adequate coverage
- Team onboarded with quick reference guide
- CodeRabbit enabled as required status check
- Fallback and emergency procedures documented
- Post-launch monitoring plan in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PRs stuck waiting for review | CodeRabbit outage | Check status.coderabbit.ai; use admin bypass |
| All PRs blocked | `request_changes_workflow: true` too aggressive | Temporarily set to `false` |
| Team pushback | Too many comments | Switch to `chill` profile |
| Emergency PR blocked | Required check blocking | Admin merge bypass or remove required check |
| Config not loading | YAML error | Run `@coderabbitai configuration` to diagnose |

## Resources
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository)
- [CodeRabbit Status Page](https://status.coderabbit.ai)

## Next Steps
For ongoing monitoring, see `coderabbit-observability`.
