# retellai-upgrade-migration

> Analyze, plan, and execute Retell AI SDK upgrades with breaking change detection and rollback procedures

## Directory Structure

```
retellai-upgrade-migration/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for SDK upgrade planning and execution |
| examples/example.py | Python | Example migration scripts and version compatibility checks |

## Summary

**Category:** operations
**Target Audience:** Tech leads, Platform engineers, Senior developers
**Trigger Phrases:** `upgrade retell`, `retell migration`, `retell breaking changes`, `update retell SDK`

### What This Skill Does

This skill guides developers through safe Retell AI SDK upgrades. It covers analyzing changelog for breaking changes, creating migration plans for API changes, testing upgrades in staging environment, executing gradual rollout, and maintaining rollback procedures for quick recovery if issues arise.

### Technical Success Criteria

- Breaking changes identified and documented
- Migration plan created with timeline
- Staging tests passing with new SDK version
- Production upgrade completed successfully
- Rollback procedure documented and tested

### Business Success Criteria

- Smooth version transitions
- Reduced upgrade-related incidents
- Complete SDK upgrades with zero production impact

## Related Skills

- retellai-ci-integration - Automated upgrade testing
- retellai-multi-env-setup - Environment-specific upgrades
- retellai-prod-checklist - Production deployment validation
