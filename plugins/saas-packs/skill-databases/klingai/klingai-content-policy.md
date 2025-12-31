# klingai-content-policy

> Implement content policy compliance for Kling AI

## Directory Structure

```
klingai-content-policy/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 content_filter.py       # Pre-generation content filter
    ├── 🐍 moderation_pipeline.py  # Post-generation moderation
    └── 📄 policy_definitions.json # Content policy rules
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with content policy guide |
| `content_filter.py` | 🐍 Python | Filter prompts before generation |
| `moderation_pipeline.py` | 🐍 Python | Moderate generated content |
| `policy_definitions.json` | 📄 JSON | Policy rule definitions |

## Summary

**Category:** enterprise
**Target Audience:** Compliance or content team
**Trigger Phrases:** `klingai content policy`, `kling ai moderation`, `klingai safe content`, `klingai compliance`

### What This Skill Does

This skill implements content policy compliance for Kling AI video generation. It covers:

- Prompt content filtering
- Prohibited content detection
- Post-generation moderation
- Policy rule definition
- Violation logging and reporting
- Human review workflow integration

### Technical Success Criteria

- Blocked policy-violating content
- Accurate content classification
- Audit trail of violations

### Business Success Criteria

- Compliant and safe video generation
- Brand protection from harmful content
- Regulatory compliance maintained

## Related Skills

- `klingai-audit-logging` - Policy violation logging
- `klingai-compliance-review` - Policy audit
- `klingai-team-setup` - Policy enforcement per team
