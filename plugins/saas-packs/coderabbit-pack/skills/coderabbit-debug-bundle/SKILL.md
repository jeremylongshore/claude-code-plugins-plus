---
name: coderabbit-debug-bundle
description: |
  Collect CodeRabbit debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for CodeRabbit problems.
  Trigger with phrases like "coderabbit debug", "coderabbit support bundle",
  "coderabbit diagnostic", "coderabbit not working evidence".
allowed-tools: Read, Bash(gh:*), Bash(git:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, debugging, support]

---
# CodeRabbit Debug Bundle

## Overview
Collect all diagnostic information needed to troubleshoot CodeRabbit issues or file a support request. Since CodeRabbit is a GitHub/GitLab App (not an SDK), debugging focuses on: App installation status, `.coderabbit.yaml` configuration validity, PR review history, and GitHub webhook delivery logs.

## Prerequisites
- GitHub CLI (`gh`) authenticated
- Repository admin access (for webhook logs)
- Access to the GitHub repository where CodeRabbit is installed

## Instructions

### Step 1: Check CodeRabbit Installation Status
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== CodeRabbit Debug Bundle ==="
echo "Repository: $OWNER/$REPO"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Check if CodeRabbit App is installed
echo "--- Installation Status ---"
INSTALL=$(gh api "repos/$OWNER/$REPO/installation" --jq '.app_slug' 2>/dev/null)
if [ "$INSTALL" = "coderabbitai" ]; then
  echo "CodeRabbit App: INSTALLED"
else
  echo "CodeRabbit App: NOT INSTALLED"
  echo "Fix: Visit https://github.com/apps/coderabbitai to install"
fi
```

### Step 2: Validate Configuration
```bash
set -euo pipefail
echo ""
echo "--- Configuration Validation ---"

# Check if .coderabbit.yaml exists
if [ -f .coderabbit.yaml ]; then
  echo ".coderabbit.yaml: FOUND ($(wc -l < .coderabbit.yaml) lines)"

  # Validate YAML syntax
  python3 -c "
import yaml, sys
try:
    config = yaml.safe_load(open('.coderabbit.yaml'))
    print('YAML syntax: VALID')

    # Check key configuration fields
    reviews = config.get('reviews', {})
    auto_review = reviews.get('auto_review', {})
    print(f'auto_review.enabled: {auto_review.get(\"enabled\", \"not set\")}')
    print(f'auto_review.drafts: {auto_review.get(\"drafts\", \"not set\")}')
    print(f'profile: {reviews.get(\"profile\", \"not set\")}')

    base_branches = auto_review.get('base_branches', [])
    if base_branches:
        print(f'base_branches: {base_branches}')
    else:
        print('base_branches: not set (reviews all branches)')

    path_filters = reviews.get('path_filters', [])
    print(f'path_filters: {len(path_filters)} rules')

    path_instructions = reviews.get('path_instructions', [])
    print(f'path_instructions: {len(path_instructions)} rules')

    chat = config.get('chat', {})
    print(f'chat.auto_reply: {chat.get(\"auto_reply\", \"not set\")}')

except yaml.YAMLError as e:
    print(f'YAML syntax: INVALID')
    print(f'Error: {e}')
    sys.exit(1)
" 2>&1
else
  echo ".coderabbit.yaml: NOT FOUND"
  echo "Fix: Create .coderabbit.yaml in repository root"
fi
```

### Step 3: Check Recent PR Review History
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"

echo ""
echo "--- Recent PR Review History ---"

# Check last 10 closed PRs for CodeRabbit reviews
for PR_NUM in $(gh api "repos/$OWNER/$REPO/pulls?state=all&per_page=10&sort=created&direction=desc" \
  --jq '.[].number'); do

  PR_TITLE=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.title' 2>/dev/null)
  PR_STATE=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.state' 2>/dev/null)

  CR_REVIEWS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")

  CR_COMMENTS=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM/comments" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")

  echo "PR #$PR_NUM ($PR_STATE): $CR_REVIEWS reviews, $CR_COMMENTS comments - $PR_TITLE"
done
```

### Step 4: Check Active Configuration via PR Comment
```markdown
# On any open PR, post this comment:
@coderabbitai configuration

# CodeRabbit will reply with the active configuration as YAML.
# Compare this with your .coderabbit.yaml to find discrepancies.
# Discrepancies usually mean:
# 1. YAML syntax error causing config to be ignored
# 2. Org-level config overriding repo config
# 3. Config not on the base branch (CodeRabbit reads from base branch)
```

### Step 5: Check GitHub Webhook Deliveries
```markdown
# In GitHub UI:
1. Go to repo > Settings > Webhooks
2. Find the CodeRabbit webhook (coderabbit.ai endpoint)
3. Click "Recent Deliveries"
4. Look for:
   - 200 response codes (success)
   - 4xx/5xx codes (errors)
   - Missing deliveries for PR events

# Common webhook issues:
# - 401: App credentials expired → reinstall
# - 404: Webhook URL changed → reinstall
# - No deliveries: Webhook was deleted → reinstall App
```

### Step 6: Compile Support Bundle
```bash
set -euo pipefail
OWNER="${1:-your-org}"
REPO="${2:-your-repo}"
BUNDLE="coderabbit-debug-$(date +%Y%m%d-%H%M%S).txt"

{
  echo "=== CodeRabbit Debug Bundle ==="
  echo "Repository: $OWNER/$REPO"
  echo "Generated: $(date -u)"
  echo "Git branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
  echo "Git remote: $(git remote get-url origin 2>/dev/null || echo 'N/A')"
  echo ""

  echo "--- .coderabbit.yaml ---"
  cat .coderabbit.yaml 2>/dev/null || echo "NOT FOUND"
  echo ""

  echo "--- App Installation ---"
  gh api "repos/$OWNER/$REPO/installation" 2>/dev/null || echo "NOT INSTALLED"
  echo ""

  echo "--- Last 5 PRs ---"
  gh api "repos/$OWNER/$REPO/pulls?state=all&per_page=5" \
    --jq '.[] | "#\(.number) [\(.state)] \(.title) (by \(.user.login))"' 2>/dev/null
  echo ""

  echo "--- GitHub Actions Status ---"
  gh run list --repo "$OWNER/$REPO" --limit 5 2>/dev/null || echo "N/A"
} > "$BUNDLE"

echo "Debug bundle saved: $BUNDLE"
echo "Review for sensitive data before sharing with support."
```

## Output
- Installation status verified
- Configuration validated for syntax and completeness
- PR review history showing CodeRabbit activity
- Active configuration compared with file on disk
- Debug bundle file ready for support ticket

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `gh api` returns 404 | Wrong org/repo or no access | Verify repo name and `gh auth status` |
| No CodeRabbit reviews found | App not installed on repo | Install from github.com/apps/coderabbitai |
| YAML validation fails | Syntax error in config | Fix YAML syntax, validate before committing |
| Webhook deliveries empty | App was uninstalled/reinstalled | Check webhook exists in repo settings |

## Resources
- [CodeRabbit FAQ](https://docs.coderabbit.ai/faq)
- [CodeRabbit Status Page](https://status.coderabbit.ai)
- [CodeRabbit Discord](https://discord.gg/coderabbit)
- [CodeRabbit Support Email](mailto:support@coderabbit.ai)

## Next Steps
For common error patterns and fixes, see `coderabbit-common-errors`.
