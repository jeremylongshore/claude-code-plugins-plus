---
name: windsurf-deploy-integration
description: |
  Deploy applications using Windsurf's built-in deployment features and Cascade automation.
  Use when deploying apps from Windsurf, configuring Netlify/Vercel integration,
  or building deployment workflows with Cascade.
  Trigger with phrases like "deploy windsurf", "windsurf deploy",
  "windsurf netlify", "windsurf vercel", "cascade deploy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, deployment, netlify, vercel]

---
# Windsurf Deploy Integration

## Overview
Windsurf offers native deployment integration (starting with Netlify) that lets you deploy directly from the IDE. Combined with Cascade workflows, you can automate the entire build-test-deploy pipeline without leaving the editor.

## Prerequisites
- Windsurf Pro plan or higher
- Deployment platform account (Netlify, Vercel, or cloud provider)
- Application ready to deploy
- Git repository configured

## Instructions

### Step 1: Use Windsurf's Native Deploy (Netlify)

Windsurf has a first-party Netlify integration:

```
1. Open Cascade (Cmd/Ctrl+L)
2. Prompt: "Deploy this project to Netlify"
3. Cascade runs the build, connects to Netlify, and deploys
4. Preview URL appears in Cascade output
5. Click to verify in browser or use in-IDE Preview
```

For first-time setup:
```
Cascade prompt: "Set up Netlify deployment for this Next.js project.
Configure build command, output directory, and environment variables."
```

### Step 2: Create a Deployment Workflow

```markdown
<!-- .windsurf/workflows/deploy-staging.md -->
---
name: deploy-staging
description: Build, test, and deploy to staging
---

## Pre-Deploy Checks
// turbo-all
1. Run `git status` — abort if uncommitted changes
2. Run `npm run typecheck` — abort if type errors
3. Run `npm test` — abort if test failures
4. Run `npm run lint` — abort if lint errors

## Build and Deploy
5. Run `npm run build`
6. Run `npx netlify deploy --dir=dist --site=$NETLIFY_SITE_ID`
   Or: `npx vercel --yes`

## Post-Deploy Verification
7. Run `curl -sf $DEPLOY_URL/health | jq .`
8. Report: deploy URL, build time, health check result
```

### Step 3: Vercel Deployment via Cascade

```
Cascade prompt: "Deploy this project to Vercel.
- Use the production branch for prod deploys
- Set these environment variables: DATABASE_URL, API_KEY
- Configure custom domain: app.example.com"
```

Cascade will run:
```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy (Cascade handles interactive prompts)
vercel --yes

# Set environment variables
vercel env add DATABASE_URL production
vercel env add API_KEY production

# Configure domain
vercel domains add app.example.com
```

### Step 4: Cloud Provider Deployment via Cascade

```markdown
<!-- AWS deployment workflow -->
Cascade prompt: "Deploy this Express API to AWS using:
1. Docker container on ECS Fargate
2. ECR for container registry
3. Application Load Balancer
4. RDS PostgreSQL for database
Generate the Dockerfile, task definition, and deployment script."
```

```markdown
<!-- Google Cloud Run deployment -->
Cascade prompt: "Deploy this to Cloud Run:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run with 512MB memory, 1 CPU
4. Set environment variables from .env.production"
```

### Step 5: Preview Deployments for PRs

```yaml
# .github/workflows/preview-deploy.yml
name: Preview Deploy
on: pull_request

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - name: Deploy preview
        run: npx netlify deploy --dir=dist --alias=pr-${{ github.event.number }}
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
      - name: Comment PR with preview URL
        run: |
          gh pr comment ${{ github.event.number }} \
            --body "Preview: https://pr-${{ github.event.number }}--your-site.netlify.app"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Step 6: Use Previews to Verify Before Deploy

```
1. Run build locally: Cascade > "Build and preview the app"
2. Windsurf opens in-IDE Preview tab
3. Click through pages, verify functionality
4. Send broken elements to Cascade: "Fix the layout on mobile"
5. Once Preview looks correct: Cascade > "Deploy to staging"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy fails on build | Missing dependencies | Check `npm ci` runs clean |
| Environment variables missing | Not set in platform | Add via CLI or dashboard |
| Preview deploy 404 | Wrong output directory | Check build config: `dist/`, `.next/`, `build/` |
| Netlify integration not available | Older Windsurf version | Update Windsurf to latest |
| Cascade can't deploy | No platform CLI installed | Install netlify-cli, vercel, or gcloud |

## Examples

### Quick Deploy Commands
```
Cascade: "Deploy to Netlify production"
Cascade: "Deploy to Vercel with preview URL"
Cascade: "Build Docker image and push to ECR"
Cascade: "Deploy to Cloud Run with 1GB memory"
```

### Rollback via Cascade
```
Cascade: "Roll back the Netlify deployment to the previous version"
Cascade: "Revert Vercel to the last successful production deploy"
```

## Resources
- [Windsurf + Netlify Integration](https://www.netlify.com/press/windsurf-netlify-ai-ide-native-deployment-integration/)
- [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- [Windsurf Previews](https://docs.windsurf.com/windsurf/previews)

## Next Steps
For multi-environment setup, see `windsurf-multi-env-setup`.
