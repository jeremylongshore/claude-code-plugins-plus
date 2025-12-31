# klingai-team-setup

> Configure Kling AI for team and organization use

## Directory Structure

```
klingai-team-setup/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 team_manager.py         # Team management utilities
    ├── 🐍 rbac_config.py          # Role-based access control
    └── 📄 onboarding_guide.md     # Team onboarding documentation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with team configuration guide |
| `team_manager.py` | 🐍 Python | Manage team members and roles |
| `rbac_config.py` | 🐍 Python | Configure role-based access |
| `onboarding_guide.md` | 📄 Markdown | Team member onboarding steps |

## Summary

**Category:** enterprise
**Target Audience:** Team lead or admin
**Trigger Phrases:** `klingai team`, `kling ai organization`, `klingai access`, `manage klingai users`

### What This Skill Does

This skill configures Kling AI for team and organization use. It covers:

- Organization account setup
- Role-based access control (RBAC)
- Project and workspace isolation
- API key management per team/project
- Usage quotas per team
- Team onboarding workflow

### Technical Success Criteria

- Role-based access with project isolation
- API keys scoped to teams/projects
- Quota enforcement per team

### Business Success Criteria

- Organized team collaboration on video projects
- Clear access boundaries
- Streamlined onboarding process

## Related Skills

- `klingai-cost-controls` - Per-team cost limits
- `klingai-usage-analytics` - Team usage reports
- `klingai-audit-logging` - Team activity auditing
