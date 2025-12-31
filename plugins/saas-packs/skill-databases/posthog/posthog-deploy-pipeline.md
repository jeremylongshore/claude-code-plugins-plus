# posthog-deploy-pipeline

> Implement deployment pipeline with PostHog feature flag integration for safe releases

## Directory Structure

```
posthog-deploy-pipeline/
├── SKILL.md
└── examples/
    ├── deploy_workflow.yml
    ├── rollout_strategy.md
    ├── rollback_script.sh
    └── deployment_metrics.ts
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for feature flag deployment pipelines |
| deploy_workflow.yml | YAML | Complete deployment workflow with feature flag gates |
| rollout_strategy.md | Markdown | Progressive rollout strategies using PostHog |
| rollback_script.sh | Shell | Automated rollback script triggered by feature flags |
| deployment_metrics.ts | TypeScript | Capture deployment metrics for monitoring |

## Summary

**Category:** CI/CD
**Target Audience:** Release engineers managing safe deployments with feature flag-controlled rollouts
**Trigger Phrases:** "posthog deployment", "feature flag rollout", "safe release posthog", "posthog deploy pipeline", "progressive rollout posthog", "posthog release management"

---

**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**License:** MIT
**Version:** 1.0.0
