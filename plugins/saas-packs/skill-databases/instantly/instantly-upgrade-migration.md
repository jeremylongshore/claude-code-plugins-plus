# instantly-upgrade-migration

> Migrate between Instantly API versions or plans without disrupting active campaigns

## Directory Structure

```
instantly-upgrade-migration/
├── SKILL.md
└── examples/
    ├── migration_plan.md
    ├── migrate_api_version.py
    ├── data_backup.py
    └── validation_post_migration.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Migration planning and execution guide |
| migration_plan.md | Markdown | Step-by-step migration planning template |
| migrate_api_version.py | Python | API version migration with compatibility layer |
| data_backup.py | Python | Backup campaign data before migration |
| validation_post_migration.py | Python | Validate successful migration completion |

## Summary

**Category:** CI/CD
**Target Audience:** Platform engineers managing Instantly upgrades
**Trigger Phrases:** "upgrade instantly api", "migrate instantly version", "instantly plan upgrade", "api migration instantly", "upgrade instantly without downtime"
**Definition of Success (Technical):** Migration completes without data loss or downtime
**Definition of Success (Business):** Seamless upgrades without disrupting active campaigns
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
