# exa-multi-env-setup

## Skill Scaffold

```
exa-multi-env-setup/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure Exa across development, staging, and production environments with environment-specific API keys and settings.
**Workflow:** Enterprise setup skill - establishes proper environment isolation.
**Relates to:** Follows exa-security-basics; prerequisite for exa-enterprise-scaling

## Summary

This skill configures multi-environment Exa setup: separate API keys per environment (dev/staging/prod), environment detection and configuration loading, secret manager integration (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault), environment-specific rate limits and caching, production safeguards (stricter error handling, alerting), and configuration validation on startup. Ensures complete environment isolation with zero cross-environment incidents.
