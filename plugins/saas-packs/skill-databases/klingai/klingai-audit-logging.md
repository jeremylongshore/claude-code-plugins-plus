# klingai-audit-logging

> Implement comprehensive audit logging for operations

## Directory Structure

```
klingai-audit-logging/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 audit_logger.py         # Audit logging implementation
    ├── 🐍 log_exporter.py         # Export logs for compliance
    └── 🐍 integrity_checker.py    # Log integrity verification
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with audit logging guide |
| `audit_logger.py` | 🐍 Python | Comprehensive audit logging |
| `log_exporter.py` | 🐍 Python | Export logs for auditors |
| `integrity_checker.py` | 🐍 Python | Verify log integrity |

## Summary

**Category:** enterprise
**Target Audience:** Security or compliance team
**Trigger Phrases:** `klingai audit`, `kling ai logging`, `klingai compliance logs`, `track klingai usage`

### What This Skill Does

This skill implements comprehensive audit logging for Kling AI operations. It covers:

- All API operations logged
- User/service attribution
- Immutable log storage
- Log integrity verification (hashing)
- Retention policies
- Export formats for auditors
- Integration with SIEM systems

### Technical Success Criteria

- Complete audit trail with integrity verification
- All operations attributed to users/services
- Tamper-evident logging

### Business Success Criteria

- Compliance-ready audit documentation
- Forensic investigation capability
- Regulatory audit readiness

## Related Skills

- `klingai-compliance-review` - Audit preparation
- `klingai-content-policy` - Policy violation logging
- `klingai-usage-analytics` - Usage analytics from logs
