---
name: replit-ci-integration
description: |
  Configure CI/CD for Replit with GitHub Actions, automated testing, and deploy-on-push.
  Use when setting up automated testing, GitHub integration for Replit,
  or continuous deployment pipelines that deploy to Replit.
  Trigger with phrases like "replit CI", "replit GitHub Actions",
  "replit automated deploy", "CI replit", "replit GitHub".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, ci-cd, github-actions, automation]

---
# Replit CI Integration

## Overview
Set up CI/CD for Replit apps: GitHub repo connected to Replit, automated testing via GitHub Actions, deploy-on-push, and post-deploy health verification. Replit supports direct GitHub import and auto-sync.

## Prerequisites
- GitHub repository with Actions enabled
- Replit App connected to GitHub (Settings > Git > Connect)
- GitHub Secrets configured for deploy verification

## Instructions

### Step 1: Connect Replit to GitHub
```markdown
1. In your Repl, click "Git" in the sidebar
2. Click "Connect to GitHub"
3. Authorize Replit GitHub App
4. Select your repository
5. Changes pushed to GitHub auto-sync to Replit

Alternative: Import from GitHub
1. Create new Repl > "Import from GitHub"
2. Paste repo URL
3. Replit clones and configures automatically
```

### Step 2: GitHub Actions — Test on PR
```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - run: npm run lint
      - run: npm run build
```

### Step 3: Deploy Verification After Push
Replit auto-deploys when you push to the connected branch. Verify the deployment is healthy:

```yaml
# .github/workflows/deploy-verify.yml
name: Verify Deployment

on:
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    # Wait for Replit to pick up the push and deploy
    steps:
      - name: Wait for deployment
        run: sleep 60

      - name: Health check
        run: |
          DEPLOY_URL="${{ secrets.REPLIT_DEPLOY_URL }}"
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOY_URL/health")
          if [ "$STATUS" != "200" ]; then
            echo "Health check failed: HTTP $STATUS"
            exit 1
          fi
          echo "Deployment healthy"

      - name: Response time check
        run: |
          DEPLOY_URL="${{ secrets.REPLIT_DEPLOY_URL }}"
          TIME=$(curl -s -o /dev/null -w "%{time_total}" "$DEPLOY_URL/health")
          echo "Response time: ${TIME}s"
          # Alert if response > 5 seconds (cold start)
          if (( $(echo "$TIME > 5" | bc -l) )); then
            echo "WARNING: Slow response (possible cold start)"
          fi
```

### Step 4: Store Deployment Secrets
```bash
# Set GitHub secrets for deploy verification
gh secret set REPLIT_DEPLOY_URL --body "https://your-app.replit.app"

# Optional: Replit API token for advanced deployments
gh secret set REPLIT_TOKEN --body "your-replit-api-token"
```

### Step 5: Branch Protection
```yaml
# Require tests to pass before merge
# In GitHub: Settings > Branches > Branch protection rules

# Required status checks:
required_status_checks:
  - "test"

# Recommended settings:
# - Require pull request reviews before merging
# - Require status checks to pass before merging
# - Require branches to be up to date before merging
```

### Step 6: GitHub Actions — Deploy from GitHub Repo
For repos not directly connected to Replit, deploy via GitHub Import:

```yaml
# .github/workflows/deploy-replit.yml
name: Deploy to Replit

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests first
        run: |
          npm ci
          npm test
          npm run build

      - name: Trigger Replit deployment
        run: |
          # Replit auto-deploys from connected GitHub repos
          # For manual trigger, use Replit API:
          curl -X POST \
            "https://replit.com/api/v1/repls/${{ secrets.REPL_ID }}/deploy" \
            -H "Authorization: Bearer ${{ secrets.REPLIT_TOKEN }}" \
            -H "Content-Type: application/json"

      - name: Verify deployment
        run: |
          sleep 90  # Wait for build + deploy
          curl -sf "${{ secrets.REPLIT_DEPLOY_URL }}/health"
```

### Step 7: Python CI Variant
```yaml
# .github/workflows/test-python.yml
name: Test Python

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -v
      - run: python -m flake8 .
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| GitHub sync not working | App not connected | Reconnect in Replit Git settings |
| Deploy verification timeout | Slow Autoscale cold start | Increase sleep, or use Reserved VM |
| Tests pass but deploy fails | Build step missing | Add `build` to `.replit` deployment section |
| Secret not found in Actions | Not set in GitHub | `gh secret set` with correct name |

## Resources
- [Deploying from GitHub](https://docs.replit.com/hosting/deployments/deploying-a-github-repository)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Replit Git Integration](https://docs.replit.com/replit-workspace/configuring-repl)

## Next Steps
For deployment patterns, see `replit-deploy-integration`.
