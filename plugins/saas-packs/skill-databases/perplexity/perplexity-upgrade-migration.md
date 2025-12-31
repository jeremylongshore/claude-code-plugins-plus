# perplexity-upgrade-migration

> Migrate and upgrade Perplexity integrations safely

## Directory Structure

```
perplexity-upgrade-migration/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── migration_guide.md      # Version migration documentation
    ├── upgrade_script.py       # Automated upgrade script
    ├── compatibility_check.py  # Check for breaking changes
    └── rollback_plan.md        # Rollback procedures
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with migration guidance |
| `migration_guide.md` | Markdown | Version-to-version migration steps |
| `upgrade_script.py` | Python | Automated upgrade and testing |
| `compatibility_check.py` | Python | Check for breaking changes |
| `rollback_plan.md` | Markdown | Rollback procedures if issues occur |

## Summary

**Category:** operations
**Target Audience:** Developer upgrading integration
**Trigger Phrases:** `perplexity upgrade`, `perplexity migrate`, `perplexity update`, `perplexity version`

### What This Skill Does

This skill teaches safe Perplexity upgrades:

- Version compatibility checking
- Breaking change identification
- Staged rollout strategies
- Testing upgraded integrations
- Rollback procedures

### Technical Success Criteria

- Successful migration with no breaking changes
- Compatibility verified before deployment
- Rollback procedures tested

### Business Success Criteria

- Maintained stability during upgrades
- Zero downtime migrations
- Continuous access to new features

## Related Skills

- `perplexity-testing-framework` - Test after migration
- `perplexity-prod-checklist` - Verify production readiness
- `perplexity-model-selection` - New model options
