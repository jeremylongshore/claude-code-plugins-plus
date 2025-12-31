# openrouter-prod-checklist

> Pre-launch production readiness checklist for OpenRouter

## Directory Structure

```
openrouter-prod-checklist/
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
**Trigger Phrases:** `openrouter production`, `openrouter go live`, `openrouter launch checklist`, `deploy openrouter`

### What This Skill Does

This skill provides a comprehensive pre-launch checklist for OpenRouter deployments. It covers:

- Security checklist (API keys, secrets management)
- Error handling verification
- Rate limiting configuration
- Fallback chain testing
- Monitoring and alerting setup
- Cost controls verification
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

- `openrouter-install-auth` - Authentication checklist items
- `openrouter-fallback-config` - Reliability checklist items
- `openrouter-cost-controls` - Cost control checklist items
