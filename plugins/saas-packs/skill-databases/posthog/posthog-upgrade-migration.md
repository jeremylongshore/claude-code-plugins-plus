# posthog-upgrade-migration

> Upgrade PostHog SDK or self-hosted instance with minimal disruption and data continuity

## Directory Structure

```
posthog-upgrade-migration/
├── SKILL.md
└── examples/
    ├── upgrade_guide.md
    ├── migration_script.sh
    ├── compatibility_check.py
    └── rollback_plan.md
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for PostHog upgrades and migrations |
| upgrade_guide.md | Markdown | Step-by-step upgrade guide for various PostHog versions |
| migration_script.sh | Shell | Automated upgrade script with validation steps |
| compatibility_check.py | Python | Script to check API and SDK compatibility before upgrade |
| rollback_plan.md | Markdown | Rollback procedures if upgrade issues occur |

## Summary

**Category:** CI/CD
**Target Audience:** Platform engineers upgrading PostHog versions or migrating deployments
**Trigger Phrases:** "upgrade posthog", "posthog migration", "update posthog sdk", "posthog version upgrade", "migrate posthog", "posthog self-hosted upgrade"

---

**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**License:** MIT
**Version:** 1.0.0
