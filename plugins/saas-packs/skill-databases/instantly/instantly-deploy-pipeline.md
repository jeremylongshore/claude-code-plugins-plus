# instantly-deploy-pipeline

> Build automated deployment pipeline for Instantly campaign configurations with rollback

## Directory Structure

```
instantly-deploy-pipeline/
├── SKILL.md
└── examples/
    ├── deploy.py
    ├── rollback.py
    ├── deployment_config.yaml
    └── release_workflow.yml
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Deployment pipeline architecture and implementation |
| deploy.py | Python | Automated deployment script with validation |
| rollback.py | Python | Rollback mechanism for failed deployments |
| deployment_config.yaml | YAML | Deployment configuration and settings |
| release_workflow.yml | YAML | Complete release workflow for CI/CD |

## Summary

**Category:** CI/CD
**Target Audience:** Release engineers automating campaign deployments
**Trigger Phrases:** "deploy instantly campaigns", "instantly deployment pipeline", "automate instantly release", "instantly rollback", "campaign deployment automation"
**Definition of Success (Technical):** Deployments execute without manual intervention
**Definition of Success (Business):** Faster reliable releases of campaign updates
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
