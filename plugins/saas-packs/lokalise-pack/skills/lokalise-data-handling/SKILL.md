---
name: lokalise-data-handling
description: |
  Implement Lokalise translation data handling, PII management, and compliance patterns.
  Use when handling sensitive translation data, implementing data redaction,
  or ensuring compliance with privacy regulations for Lokalise integrations.
  Trigger with phrases like "lokalise data", "lokalise PII",
  "lokalise GDPR", "lokalise data retention", "lokalise privacy", "lokalise compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Data Handling

## Overview
Handle translation data correctly with privacy, compliance, and data governance best practices.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Lokalise SDK installed
- Database for audit logging
- Data classification policies

## Instructions
1. **Data Classification**
2. **Instructions**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- PII scanning for translations
- Safe logging practices
- Data retention enforcement
- Audit trail for compliance

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in translations | User-submitted content | Scan before upload |
| Token in logs | Improper logging | Use safe log wrapper |
| Audit gaps | Missing logging | Add audit calls |
| Retention violation | No cleanup | Schedule retention jobs |

## Examples
### Pre-commit PII Check
```bash
#!/bin/bash
# .husky/pre-commit

# Check for PII in translation files
node scripts/scan-translations-pii.js

if [ $? -ne 0 ]; then
  echo "PII detected in translations. Please review and remove."
  exit 1
fi
```

### Quick PII Scan
```typescript
const result = await validateBeforeUpload("./locales/en.json");
if (!result.valid) {
  console.error("Cannot upload: PII detected");
  result.findings.forEach(f => console.error(`  ${f.type}: ${f.key}`));
  process.exit(1);
}
```

## Resources
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)
- [Lokalise Privacy](https://lokalise.com/privacy-policy)

## Next Steps
For enterprise access control, see `lokalise-enterprise-rbac`.
