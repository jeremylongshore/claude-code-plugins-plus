# perplexity-audit-logging

> Implement comprehensive audit logging for search operations

## Directory Structure

```
perplexity-audit-logging/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── audit_logger.py         # Audit logging implementation
    ├── audit_schema.yaml       # Audit log schema definition
    ├── log_exporter.py         # Export logs to SIEM
    └── audit_report.py         # Audit report generation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with audit logging patterns |
| `audit_logger.py` | Python | Comprehensive audit logging |
| `audit_schema.yaml` | YAML | Audit log field definitions |
| `log_exporter.py` | Python | Export to SIEM systems |
| `audit_report.py` | Python | Generate audit reports |

## Summary

**Category:** enterprise
**Target Audience:** Security or compliance team
**Trigger Phrases:** `perplexity audit`, `perplexity logging`, `perplexity compliance logs`, `track perplexity queries`

### What This Skill Does

This skill teaches audit logging for Perplexity:

- Comprehensive query and response logging
- User attribution and timestamps
- Immutable audit trail storage
- SIEM integration
- Audit report generation

### Technical Success Criteria

- Complete audit trail with integrity verification
- Immutable log storage configured
- SIEM integration operational

### Business Success Criteria

- Compliance-ready audit documentation
- Forensic investigation capability
- Regulatory requirement satisfaction

## Related Skills

- `perplexity-data-governance` - Governance framework
- `perplexity-debug-logging` - Operational vs audit logging
- `perplexity-team-management` - User attribution
