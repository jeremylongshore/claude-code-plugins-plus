# openrouter-data-privacy

> Implement data privacy controls for OpenRouter integrations

## Directory Structure

```
openrouter-data-privacy/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 pii_detector.py         # PII detection and redaction
    ├── 🐍 data_classifier.py      # Data classification utilities
    └── ⚙️ privacy_policy.yaml     # Data handling policies
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with data privacy patterns |
| `pii_detector.py` | 🐍 Python | PII detection before sending to API |
| `data_classifier.py` | 🐍 Python | Classify data sensitivity levels |
| `privacy_policy.yaml` | ⚙️ YAML | Data handling and retention policies |

## Summary

**Category:** enterprise
**Target Audience:** Security or compliance team
**Trigger Phrases:** `openrouter privacy`, `openrouter data handling`, `openrouter PII`, `openrouter GDPR`

### What This Skill Does

This skill implements data privacy controls for OpenRouter:

- PII detection and redaction before API calls
- Data classification and handling policies
- GDPR/CCPA compliance patterns
- Data retention and deletion procedures
- Logging without sensitive data exposure

### Technical Success Criteria

- Data handling compliant with privacy policies
- PII protection measures in place
- Data routing and storage understood

### Business Success Criteria

- Meet GDPR/CCPA requirements
- Protect customer data
- Enable data subject access requests

## Related Skills

- `openrouter-compliance-review` - Compliance assessment
- `openrouter-audit-logging` - Privacy-aware logging
- `openrouter-team-setup` - Access control
