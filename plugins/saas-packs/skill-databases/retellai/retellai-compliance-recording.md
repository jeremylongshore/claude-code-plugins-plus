# retellai-compliance-recording

> Implement compliant call recording with consent management, retention policies, and audit trails

## Directory Structure

```
retellai-compliance-recording/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for compliant call recording |
| examples/example.py | Python | Example consent management and retention policy implementation |

## Summary

**Category:** enterprise
**Target Audience:** Security engineers, Compliance officers, Legal teams
**Trigger Phrases:** `retell recording compliance`, `retell TCPA`, `retell consent`, `retell call recording laws`

### What This Skill Does

This skill implements legally compliant call recording for Retell AI voice agents. It covers consent management (one-party vs two-party consent states), TCPA compliance for outbound calls, data retention policies and automated deletion, secure storage with encryption, and audit trail generation for regulatory requirements.

### Technical Success Criteria

- Consent management implemented based on jurisdiction
- Retention policies automated with configurable periods
- Recordings encrypted at rest and in transit
- Audit trail enabled for all recording access
- Deletion workflows for GDPR/CCPA requests

### Business Success Criteria

- Regulatory compliance achieved
- Reduced legal risk from improper recording
- 100% compliant call recording with full audit trail

## Related Skills

- retellai-security-basics - General security patterns
- retellai-enterprise-sso - Access control
- retellai-call-analytics - Compliant analytics on recordings
