# retellai-security-basics

> Apply security best practices for API keys, webhook secrets, and call recording access control

## Directory Structure

```
retellai-security-basics/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for Retell AI security hardening |
| examples/example.py | Python | Example showing secure API key handling and webhook verification |

## Summary

**Category:** operations
**Target Audience:** Security engineers, DevOps engineers, Platform engineers
**Trigger Phrases:** `retell security`, `retell secrets`, `secure retell`, `retell API key security`

### What This Skill Does

This skill applies security best practices for Retell AI integrations. It covers secure API key storage using environment variables or secret managers, webhook signature verification to prevent spoofing, access control for call recordings and transcripts, and audit logging for compliance requirements.

### Technical Success Criteria

- API keys stored in secure location (env vars, secret manager)
- Webhook signature verification implemented
- Call recording access properly restricted
- Audit logging enabled for API operations

### Business Success Criteria

- Reduced security incidents
- Compliance readiness for SOC2/HIPAA
- Zero credential exposure incidents, 100% webhook signature verification

## Related Skills

- retellai-install-auth - Initial secure setup
- retellai-compliance-recording - Recording compliance
- retellai-enterprise-sso - Enterprise access control
