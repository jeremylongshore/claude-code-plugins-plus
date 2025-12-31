# klingai-prod-checklist

> Pre-launch production readiness checklist for Kling AI

## Directory Structure

```
klingai-prod-checklist/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 readiness_check.py      # Automated checklist verification
    └── 📄 checklist_template.md   # Printable checklist template
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with production readiness checklist |
| `readiness_check.py` | 🐍 Python | Automated verification script |
| `checklist_template.md` | 📄 Markdown | Printable checklist for sign-off |

## Summary

**Category:** operations
**Target Audience:** DevOps engineer or developer
**Trigger Phrases:** `klingai production`, `kling ai go live`, `klingai launch checklist`, `deploy klingai`

### What This Skill Does

This skill provides a comprehensive pre-launch checklist for Kling AI deployments. It covers:

- Security checklist (API keys, secrets management)
- Error handling verification
- Rate limiting configuration
- Monitoring and alerting setup
- Backup and recovery procedures
- Documentation requirements
- Performance baseline validation

### Technical Success Criteria

- All checklist items verified and passed
- Automated verification script green
- No critical gaps in production readiness

### Business Success Criteria

- Confident production deployment
- Reduced risk of post-launch issues
- Stakeholder sign-off obtained

## Related Skills

- `klingai-install-auth` - Authentication checklist items
- `klingai-debug-bundle` - Monitoring checklist items
- `klingai-compliance-review` - Compliance checklist items
