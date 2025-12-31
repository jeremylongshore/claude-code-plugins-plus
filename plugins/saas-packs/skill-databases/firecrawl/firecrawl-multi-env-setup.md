# firecrawl-multi-env-setup

## Skill Scaffold

```
firecrawl-multi-env-setup/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure FireCrawl across development, staging, and production environments with credential management and environment isolation.
**Workflow:** Enterprise configuration skill - establishes environment-aware configuration patterns.
**Relates to:** Extends firecrawl-security-basics; foundational for firecrawl-enterprise-rbac

## Summary

This skill configures FireCrawl for multi-environment deployments. It covers environment detection and configuration loading, separate API keys per environment, environment-specific rate limits and quotas, credential management through secrets managers (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager), and production safeguards to prevent accidental cross-environment operations. This ensures proper isolation between development, staging, and production scraping pipelines.
