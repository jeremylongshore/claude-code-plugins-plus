# perplexity-team-management

> Configure Perplexity for team and organization use

## Directory Structure

```
perplexity-team-management/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── team_setup.md           # Team configuration guide
    ├── role_definitions.yaml   # Role and permission definitions
    ├── key_management.py       # API key management scripts
    └── onboarding_checklist.md # New team member onboarding
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with team management guidance |
| `team_setup.md` | Markdown | Step-by-step team configuration |
| `role_definitions.yaml` | YAML | Role and permission templates |
| `key_management.py` | Python | API key rotation and management |
| `onboarding_checklist.md` | Markdown | New member onboarding steps |

## Summary

**Category:** enterprise
**Target Audience:** Team lead or admin
**Trigger Phrases:** `perplexity team`, `perplexity organization`, `perplexity access`, `manage perplexity users`

### What This Skill Does

This skill teaches team management for Perplexity:

- Setting up team accounts and access
- Role-based permission management
- API key distribution and rotation
- Usage tracking per team member
- Onboarding new team members

### Technical Success Criteria

- Role-based access with key isolation
- API keys properly managed and rotated
- Usage tracked per user/team

### Business Success Criteria

- Organized team collaboration
- Clear accountability for usage
- Streamlined onboarding process

## Related Skills

- `perplexity-cost-controls` - Budget per team
- `perplexity-usage-analytics` - Per-team usage reports
- `perplexity-audit-logging` - Team activity audit
