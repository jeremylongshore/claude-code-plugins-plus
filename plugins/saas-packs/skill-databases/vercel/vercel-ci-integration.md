# vercel-ci-integration

## Skill Scaffold

```
vercel-ci-integration/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure Vercel CI/CD integration with GitHub Actions, automated testing, and release workflows.
**Workflow:** Set up once per repository; maintains automated testing and deployment pipeline.
**Relates to:** Supports vercel-upgrade-migration; leads to vercel-deploy-integration for platform deployment

## Summary

This skill sets up automated CI/CD pipelines for Vercel integrations using GitHub Actions. It covers workflow configuration for test automation on push/PR, secure secret management with GitHub Secrets, integration test patterns that gracefully skip when API keys aren't available, release workflows triggered by tags, and branch protection rules. The goal is 100% automated testing coverage for all Vercel integration code.
