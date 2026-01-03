# openrouter-audit-logging

> Implement comprehensive audit logging for OpenRouter API calls

## Directory Structure

```
openrouter-audit-logging/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 audit_logger.py         # Structured audit logging implementation
    ├── 🐍 compliance_reporter.py  # Compliance report generation
    └── ⚙️ audit_config.yaml       # Audit configuration schema
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with audit logging patterns |
| `audit_logger.py` | 🐍 Python | Structured audit logging with request/response capture |
| `compliance_reporter.py` | 🐍 Python | Generate compliance reports from audit logs |
| `audit_config.yaml` | ⚙️ YAML | Configuration for audit retention and policies |

## Summary

**Category:** enterprise
**Target Audience:** Security or compliance team
**Trigger Phrases:** `openrouter audit`, `openrouter logging`, `openrouter compliance logging`, `track openrouter calls`

### What This Skill Does

This skill implements comprehensive audit logging for OpenRouter operations:

- Structured logging of all API requests and responses
- Timestamp and user context tracking
- Compliance-ready log formats (JSON, SIEM integration)
- Log retention and archival policies
- Integrity verification for audit trails

### Technical Success Criteria

- Complete audit trail with timestamps and user context
- Logs searchable and exportable in compliance formats
- Integrity verification preventing log tampering

### Business Success Criteria

- Meet SOC2/HIPAA compliance requirements
- Enable security incident investigation
- Audit-ready documentation

## Related Skills

- `openrouter-compliance-review` - Compliance assessment framework
- `openrouter-data-privacy` - Data handling policies
- `openrouter-usage-analytics` - Usage tracking and reporting
