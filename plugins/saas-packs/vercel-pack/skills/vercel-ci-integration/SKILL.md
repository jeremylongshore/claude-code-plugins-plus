---
name: vercel-ci-integration
description: |
  Configure Vercel CI/CD with GitHub Actions, preview deployments, and automated testing.
  Use when setting up automated deployments, configuring preview bots,
  or integrating Vercel into your CI pipeline.
  Trigger with phrases like "vercel CI", "vercel GitHub Actions",
  "vercel automated deploy", "CI vercel", "vercel pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(vercel:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, ci-cd, github-actions, automation]

---
# Vercel CI Integration

## Overview
Set up automated Vercel deployments in GitHub Actions with preview deployments on PRs, production deploys on merge to main, and optional test gating. Covers both Vercel's built-in Git integration and custom CI pipelines using the Vercel CLI.

## Prerequisites
- GitHub repository with Actions enabled
- Vercel project linked to the repo
- `VERCEL_TOKEN` stored as GitHub Secret
- `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` from `.vercel/project.json`

## Instructions

### Step 1: Store CI Secrets in GitHub
```bash
# Get project and org IDs
cat .vercel/project.json
# {"orgId":"team_xxx","projectId":"prj_xxx"}

# Add secrets to GitHub repo
gh secret set VERCEL_TOKEN --body "your-vercel-token"
gh secret set VERCEL_ORG_ID --body "team_xxx"
gh secret set VERCEL_PROJECT_ID --body "prj_xxx"
```

### Step 2: GitHub Actions — Preview on PR
```yaml
# .github/workflows/vercel-preview.yml
name: Vercel Preview Deployment
on:
  pull_request:
    branches: [main]

jobs:
  deploy-preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel@latest

      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Build Project
        run: vercel build --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Deploy Preview
        id: deploy
        run: |
          url=$(vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }})
          echo "preview_url=$url" >> $GITHUB_OUTPUT
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Comment PR with Preview URL
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `Preview deployed: ${{ steps.deploy.outputs.preview_url }}`
            })
```

### Step 3: GitHub Actions — Production on Merge
```yaml
# .github/workflows/vercel-production.yml
name: Vercel Production Deployment
on:
  push:
    branches: [main]

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel@latest

      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Build Project
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Deploy Production
        run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Step 4: Test Gating — Run Tests Before Deploy
```yaml
# .github/workflows/vercel-gated.yml
name: Gated Vercel Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm test
      - run: npm run lint
      - run: npx tsc --noEmit

  deploy:
    needs: test  # Only deploy if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g vercel@latest
      - run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
      - run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
      - run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Step 5: Skip Builds for Non-Code Changes
```json
// vercel.json — skip build when only docs change
{
  "ignoreCommand": "git diff HEAD^ HEAD --quiet -- . ':!docs' ':!*.md' ':!.github'"
}
```

Or in the dashboard: **Settings > Git > Ignored Build Step**

### Step 6: Vercel's Built-In Git Integration (Alternative)
If you prefer Vercel's automatic deployments over custom CI:

1. Connect your GitHub repo in the Vercel dashboard
2. Vercel auto-deploys: preview on every push, production on merge to main
3. Configure in **Settings > Git**:
   - Production branch: `main`
   - Preview branches: all other branches
   - Auto-assign custom domains to production

This approach requires zero CI configuration but gives less control over test gating.

## Output
- Preview deployments on every PR with URL comment
- Production deployments on merge to main (after tests pass)
- Test gating preventing broken code from reaching production
- Build skip rules for documentation-only changes

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Error: VERCEL_TOKEN is not set` | Secret not configured | Add `VERCEL_TOKEN` as GitHub repo secret |
| `Error: Could not find project` | Wrong ORG_ID or PROJECT_ID | Check `.vercel/project.json` values |
| `vercel pull` fails | Token lacks project access | Regenerate token with correct scope |
| Preview not commenting on PR | Missing `actions/github-script` | Add the comment step with correct permissions |
| Build cache not working | CI runs on fresh runner | Use `actions/cache` for `node_modules` and `.vercel/output` |

## Resources
- [Vercel CLI in CI](https://vercel.com/docs/cli/deploying-from-cli)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Vercel Git Integration](https://vercel.com/docs/deployments/git)
- [Ignored Build Step](https://vercel.com/docs/project-configuration#ignorecommand)

## Next Steps
For deployment orchestration, see `vercel-deploy-integration`.
