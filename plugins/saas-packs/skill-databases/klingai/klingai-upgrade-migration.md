# klingai-upgrade-migration

> Migrate and upgrade Kling AI SDK versions safely

## Directory Structure

```
klingai-upgrade-migration/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 migration_script.py     # Automated migration helper
    ├── 🐍 compatibility_check.py  # Version compatibility checker
    └── 📄 changelog_parser.py     # Parse SDK changelog for breaking changes
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with migration guide |
| `migration_script.py` | 🐍 Python | Automated migration assistance |
| `compatibility_check.py` | 🐍 Python | Check code for deprecated patterns |
| `changelog_parser.py` | 🐍 Python | Extract breaking changes from changelog |

## Summary

**Category:** operations
**Target Audience:** Developer upgrading SDK
**Trigger Phrases:** `klingai upgrade`, `kling ai migration`, `update klingai sdk`, `klingai breaking changes`

### What This Skill Does

This skill guides safe SDK upgrades and migrations for Kling AI. It covers:

- Version compatibility checking
- Breaking change identification
- Code migration patterns
- Rollback procedures
- Testing upgrade in staging
- Feature flag strategies for gradual rollout

### Technical Success Criteria

- Successful SDK upgrade with no breaking changes
- Compatibility verified in staging environment
- Rollback plan tested and documented

### Business Success Criteria

- Maintained stability during upgrades
- Zero downtime migration
- Access to new features and improvements

## Related Skills

- `klingai-sdk-patterns` - SDK patterns to update
- `klingai-common-errors` - New error handling patterns
- `klingai-prod-checklist` - Post-upgrade verification
