# retellai-multi-env-setup

> Configure Retell AI across development, staging, and production environments with agent versioning

## Directory Structure

```
retellai-multi-env-setup/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for multi-environment configuration |
| examples/example.py | Python | Example environment-aware configuration and agent versioning |

## Summary

**Category:** enterprise
**Target Audience:** DevOps engineers, Platform engineers, Cloud architects
**Trigger Phrases:** `retell environments`, `retell staging`, `retell dev prod`, `retell environment setup`

### What This Skill Does

This skill configures Retell AI across multiple environments with proper isolation and promotion paths. It covers environment-specific API keys and agent configurations, agent versioning for safe rollouts, promotion workflows from dev to staging to production, environment detection in code, and production safeguards.

### Technical Success Criteria

- Multi-environment config structure established
- Environment detection working correctly
- Agent versions tracked per environment
- Promotion workflow documented
- Production safeguards preventing accidental changes

### Business Success Criteria

- Environment isolation preventing cross-contamination
- Reduced production incidents from config errors
- Zero cross-environment configuration incidents

## Related Skills

- retellai-ci-integration - Automated environment promotion
- retellai-prod-checklist - Production deployment validation
- retellai-security-basics - Environment-specific secrets
