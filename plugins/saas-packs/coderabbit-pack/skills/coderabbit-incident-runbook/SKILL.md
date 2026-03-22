---
name: coderabbit-incident-runbook
description: |
  Execute CodeRabbit incident response procedures when reviews stop working or block PRs.
  Use when CodeRabbit is down, reviews are not posting, PRs are blocked by stale checks,
  or CodeRabbit is producing incorrect reviews.
  Trigger with phrases like "coderabbit incident", "coderabbit outage",
  "coderabbit down", "coderabbit broken", "coderabbit emergency", "coderabbit not reviewing".
allowed-tools: Read, Grep, Bash(gh:*), Bash(curl:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, incident-response, runbook]

---
# CodeRabbit Incident Runbook

## Overview
Rapid incident response procedures when CodeRabbit stops reviewing PRs, blocks merges, or behaves incorrectly. Since CodeRabbit is a managed SaaS service, incidents fall into two categories: (1) CodeRabbit service outage (check their status page), or (2) local configuration/permission issues (fix on your side).

## Severity Levels

| Level | Symptom | Response Time | Action |
|-------|---------|---------------|--------|
| P1 | PRs blocked, cannot merge | Immediate | Bypass check, notify team |
| P2 | Reviews not posting | < 1 hour | Diagnose installation |
| P3 | Reviews delayed (> 15 min) | < 4 hours | Check service status |
| P4 | Incorrect reviews | Next business day | Tune configuration |

## Instructions

### Step 1: Quick Triage (2 Minutes)
```bash
set -euo pipefail
echo "=== CodeRabbit Quick Triage ==="

# 1. Check CodeRabbit status page
echo "--- Service Status ---"
STATUS=$(curl -sf https://status.coderabbit.ai 2>/dev/null && echo "REACHABLE" || echo "UNREACHABLE")
echo "Status page: $STATUS"
echo "Check manually: https://status.coderabbit.ai"

echo ""
echo "--- Decision ---"
echo "If status.coderabbit.ai shows an incident:"
echo "  → CodeRabbit-side issue. Wait for resolution. Use bypass if blocking."
echo ""
echo "If status page is green:"
echo "  → Local issue. Check installation, config, permissions."
```

### Step 2: P1 Emergency -- PRs Blocked
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== P1: EMERGENCY BYPASS ==="

# Option A: Remove CodeRabbit from required checks (temporary)
echo "--- Option A: Remove Required Check ---"
echo "gh api repos/$OWNER/$REPO/branches/main/protection --method DELETE"
echo "(This removes ALL branch protection. Re-apply after incident.)"

echo ""
echo "--- Option B: Admin Merge ---"
echo "Org admins can merge even when checks fail."
echo "Settings > Branches > Branch protection > uncheck 'Include administrators'"

echo ""
echo "--- Option C: Force Re-Review ---"
echo "On the blocked PR, post:"
echo "  @coderabbitai full review"
echo ""
echo "Wait 5 minutes. If no response, use Option A or B."
```

### Step 3: P2 -- Reviews Not Posting
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== P2: Reviews Not Posting ==="

# Check installation
echo "--- Installation Check ---"
INSTALLED=$(gh api "repos/$OWNER/$REPO/installation" --jq '.app_slug' 2>/dev/null || echo "NOT_FOUND")
echo "CodeRabbit App: $INSTALLED"

if [ "$INSTALLED" != "coderabbitai" ]; then
  echo "FIX: Reinstall CodeRabbit at https://github.com/apps/coderabbitai"
  exit 1
fi

# Check recent PRs for reviews
echo ""
echo "--- Recent PR Reviews ---"
for PR_NUM in $(gh api "repos/$OWNER/$REPO/pulls?state=open&per_page=5" --jq '.[].number'); do
  TITLE=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.title' 2>/dev/null)
  CR=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  echo "PR #$PR_NUM ($TITLE): $CR CodeRabbit reviews"
done

echo ""
echo "--- Config Check ---"
if [ -f .coderabbit.yaml ]; then
  python3 -c "
import yaml
config = yaml.safe_load(open('.coderabbit.yaml'))
reviews = config.get('reviews', {})
auto = reviews.get('auto_review', {})
print(f'auto_review.enabled: {auto.get(\"enabled\", \"not set\")}')
print(f'auto_review.drafts: {auto.get(\"drafts\", \"not set\")}')
print(f'base_branches: {auto.get(\"base_branches\", \"all branches\")}')
print(f'ignore_title_keywords: {auto.get(\"ignore_title_keywords\", \"none\")}')
" 2>&1
else
  echo ".coderabbit.yaml: NOT FOUND (CodeRabbit uses defaults)"
fi
```

### Step 4: P3 -- Reviews Delayed
```markdown
# Reviews typically take:
# - Small PRs (< 200 lines): 2-3 minutes
# - Medium PRs (200-500 lines): 3-7 minutes
# - Large PRs (500-1000 lines): 7-12 minutes
# - Very large PRs (1000+ lines): 12-15+ minutes

# If reviews are delayed beyond expected time:
1. Check status.coderabbit.ai for service degradation
2. Try forcing a re-review: @coderabbitai full review
3. Check if the PR has an unusual number of files (> 100)
4. Check if the PR is a draft (drafts may be skipped)
5. Verify the PR targets a configured base branch

# If consistently slow:
# - Split PRs to under 500 lines
# - Add path_filters to exclude large generated files
```

### Step 5: P4 -- Incorrect or Noisy Reviews
```yaml
# If CodeRabbit is posting irrelevant or incorrect reviews:

# 1. Reply to the incorrect comment explaining why it's wrong:
# "We intentionally do this because [reason]. Don't flag this pattern."
# CodeRabbit creates a learning from your feedback.

# 2. Adjust the review profile:
reviews:
  profile: "chill"      # Reduce comment volume

# 3. Add contextual instructions to prevent misguided comments:
  path_instructions:
    - path: "src/legacy/**"
      instructions: |
        Legacy code. ONLY flag security issues and bugs.
        Do NOT comment on style, naming, or refactoring.
```

### Step 6: Communication Template
```markdown
# Internal Slack/Teams message:

## CodeRabbit Incident

**Status**: [INVESTIGATING | MITIGATING | RESOLVED]
**Impact**: [CodeRabbit reviews are not posting / PRs are blocked / Reviews are delayed]
**Service status**: [status.coderabbit.ai shows {status}]

**Current action**: [Checking installation / Applied bypass / Waiting for service recovery]

**Workaround**: [Admin merge available / Required check temporarily removed]

**Next update**: [time]
```

### Step 7: Post-Incident Recovery
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== Post-Incident Recovery ==="

# 1. Re-enable branch protection if it was removed
echo "--- Re-enabling Branch Protection ---"
gh api "repos/$OWNER/$REPO/branches/main/protection" \
  --method PUT \
  --field 'required_status_checks={"strict":true,"contexts":["coderabbitai"]}' \
  --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
  --field 'enforce_admins=false' \
  --field 'restrictions=null'

echo "Branch protection restored."

# 2. Trigger re-review on any PRs that were merged without review
echo ""
echo "--- PRs Merged During Incident ---"
echo "Review these PRs manually for any issues:"
gh api "repos/$OWNER/$REPO/pulls?state=closed&per_page=10" \
  --jq '.[] | select(.merged_at != null) | "#\(.number) \(.title) (merged \(.merged_at))"'

# 3. Verify CodeRabbit is working again
echo ""
echo "--- Verification ---"
echo "Create a test PR or post '@coderabbitai full review' on an open PR."
```

## Output
- Incident severity classified and appropriate response executed
- Emergency bypass applied if PRs are blocked
- Root cause identified (service outage vs local issue)
- Communication sent to stakeholders
- Branch protection restored after incident
- Post-incident review of PRs merged without review

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cannot remove branch protection | Not an org admin | Escalate to org admin |
| Status page unreachable | Network issue | Try from phone or VPN |
| Re-review command ignored | CodeRabbit outage | Use admin bypass |
| Branch protection restore fails | API permissions | Use GitHub UI instead |

## Resources
- [CodeRabbit Status Page](https://status.coderabbit.ai)
- [CodeRabbit Discord](https://discord.gg/coderabbit)
- [CodeRabbit Support](mailto:support@coderabbit.ai)
- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)

## Next Steps
For data handling, see `coderabbit-data-handling`.
