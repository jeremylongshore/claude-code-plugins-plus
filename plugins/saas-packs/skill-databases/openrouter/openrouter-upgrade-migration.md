# openrouter-upgrade-migration

> Migrate and upgrade OpenRouter integrations safely

## Directory Structure

```
openrouter-upgrade-migration/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 migration_script.py     # Automated migration helper
    └── 🐍 compatibility_check.py  # Version compatibility checker
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with migration guide |
| `migration_script.py` | 🐍 Python | Automated migration assistance |
| `compatibility_check.py` | 🐍 Python | Check code for deprecated patterns |

## Summary

**Category:** operations
**Target Audience:** Developer upgrading SDK
**Trigger Phrases:** `openrouter upgrade`, `openrouter migration`, `update openrouter`, `openrouter breaking changes`

### What This Skill Does

This skill guides safe upgrades and migrations for OpenRouter integrations. It covers:

- API version changes
- Model deprecation handling
- SDK upgrade patterns
- Rollback procedures
- Testing upgrade in staging
- Feature flag strategies

### Technical Success Criteria

- Successful migration with no breaking changes
- Compatibility verified in staging environment
- Rollback plan tested and documented

### Business Success Criteria

- Maintained stability during upgrades
- Zero downtime migration
- Access to new features and models

## Related Skills

- `openrouter-sdk-patterns` - SDK patterns to update
- `openrouter-model-catalog` - New model availability
- `openrouter-prod-checklist` - Post-upgrade verification
