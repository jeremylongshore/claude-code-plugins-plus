---
name: speak-data-handling
description: |
  Implement Speak PII handling, audio data retention, and GDPR/CCPA compliance patterns.
  Use when handling user learning data, implementing audio retention policies,
  or ensuring privacy compliance for language learning applications.
  Trigger with phrases like "speak data", "speak PII",
  "speak GDPR", "speak data retention", "speak privacy", "speak audio privacy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Speak Data Handling

## Overview
Handle sensitive user data and audio recordings correctly when integrating with Speak language learning.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Speak SDK with data export capabilities
- Database for audit logging
- Scheduled job infrastructure for cleanup
- Audio storage with encryption

## Instructions
1. **Data Classification**
2. **Audio Data Privacy**
3. **Learning Data Handling**
4. **GDPR/CCPA Compliance**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Audio consent management
- Secure audio storage with encryption
- PII detection and sanitization
- Retention policy enforcement
- GDPR/CCPA compliance (export/delete)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in lessons | User shared personal info | Sanitize before storage |
| Audio not deleted | Storage error | Retry with exponential backoff |
| Export incomplete | Timeout | Use streaming export |
| Consent not recorded | Race condition | Use transactions |

## Examples
See `references/implementation-guide.md` for detailed examples.

## Resources
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)
- [Speak Privacy Guide](https://developer.speak.com/docs/privacy)
- [Audio Privacy Best Practices](https://developer.speak.com/docs/audio-privacy)

## Next Steps
For enterprise access control, see `speak-enterprise-rbac`.
