# firecrawl-deploy-pipeline

## Skill Scaffold

```
firecrawl-deploy-pipeline/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Deploy FireCrawl scraping pipelines to cloud functions, containers, and scheduled jobs on major cloud platforms.
**Workflow:** Deployment skill - packages and deploys scraping pipelines to production infrastructure.
**Relates to:** Follows firecrawl-ci-integration; integrates with firecrawl-multi-env-setup for environment management

## Summary

This skill deploys FireCrawl scraping pipelines to production infrastructure. It covers deployment to AWS Lambda, Google Cloud Functions, and Azure Functions for serverless execution, Docker container deployment for persistent workers, and scheduled job configuration using cloud schedulers. Each deployment pattern includes secrets management, environment configuration, and health check endpoints for monitoring.
