# openrouter-team-setup

> Configure OpenRouter for team and organization use

## Directory Structure

```
openrouter-team-setup/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 team_manager.py         # Team management utilities
    ├── 🐍 key_isolation.py        # Key isolation per team
    └── 📄 onboarding_guide.md     # Team onboarding documentation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with team configuration guide |
| `team_manager.py` | 🐍 Python | Manage team API keys |
| `key_isolation.py` | 🐍 Python | Isolate keys per team/project |
| `onboarding_guide.md` | 📄 Markdown | Team member onboarding steps |

## Summary

**Category:** enterprise
**Target Audience:** Team lead or admin
**Trigger Phrases:** `openrouter team`, `openrouter organization`, `openrouter access`, `manage openrouter users`

### What This Skill Does

This skill configures OpenRouter for team and organization use. It covers:

- Multiple API key management
- Key naming and organization
- Credit limits per key
- Usage tracking per team
- Key rotation procedures
- Team onboarding workflow

### Technical Success Criteria

- Keys properly organized by team/project
- Credit limits enforced per key
- Usage attributable to teams

### Business Success Criteria

- Organized team collaboration
- Clear cost attribution
- Streamlined onboarding process

## Related Skills

- `openrouter-cost-controls` - Per-team cost limits
- `openrouter-usage-analytics` - Team usage reports
- `openrouter-audit-logging` - Team activity auditing
