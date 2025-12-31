# perplexity-data-governance

> Implement data governance controls for Perplexity usage

## Directory Structure

```
perplexity-data-governance/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── governance_policy.md    # Data governance policy template
    ├── query_filter.py         # Filter sensitive queries
    ├── data_classification.yaml # Data classification rules
    └── retention_policy.py     # Data retention implementation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with governance patterns |
| `governance_policy.md` | Markdown | Data governance policy template |
| `query_filter.py` | Python | Filter and sanitize queries |
| `data_classification.yaml` | YAML | Define data classification levels |
| `retention_policy.py` | Python | Implement data retention rules |

## Summary

**Category:** enterprise
**Target Audience:** Security or compliance team
**Trigger Phrases:** `perplexity governance`, `perplexity compliance`, `perplexity data policy`, `perplexity privacy`

### What This Skill Does

This skill teaches data governance for Perplexity:

- Data classification for queries
- Sensitive data filtering
- Retention and deletion policies
- Access control governance
- Compliance framework mapping

### Technical Success Criteria

- Proper data handling with governance controls
- Sensitive data filtered from queries
- Retention policies enforced

### Business Success Criteria

- Compliant search operations
- Reduced data risk exposure
- Audit-ready documentation

## Related Skills

- `perplexity-audit-logging` - Governance audit trails
- `perplexity-team-management` - Access governance
- `perplexity-reference-architecture` - Governance in architecture
