# perplexity-prod-checklist

> Pre-launch production readiness checklist for Perplexity

## Directory Structure

```
perplexity-prod-checklist/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── checklist.md            # Complete production checklist
    ├── readiness_check.py      # Automated readiness verification
    ├── security_audit.md       # Security considerations
    └── launch_runbook.md       # Production launch runbook
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with checklist guidance |
| `checklist.md` | Markdown | Complete pre-launch checklist |
| `readiness_check.py` | Python | Automated production readiness script |
| `security_audit.md` | Markdown | Security review checklist |
| `launch_runbook.md` | Markdown | Step-by-step launch procedures |

## Summary

**Category:** operations
**Target Audience:** DevOps engineer or developer
**Trigger Phrases:** `perplexity production`, `perplexity launch`, `perplexity deploy`, `perplexity checklist`

### What This Skill Does

This skill provides production readiness verification:

- Authentication and key security
- Rate limiting and error handling
- Monitoring and alerting setup
- Caching and performance
- Backup and recovery procedures
- Security review items

### Technical Success Criteria

- All checklist items verified and passed
- Automated readiness checks passing
- Security review completed

### Business Success Criteria

- Confident production deployment
- Reduced launch-day incidents
- Stakeholder sign-off obtained

## Related Skills

- `perplexity-monitoring-alerts` - Set up monitoring
- `perplexity-rate-limits` - Verify rate limit handling
- `perplexity-common-errors` - Error handling verified
