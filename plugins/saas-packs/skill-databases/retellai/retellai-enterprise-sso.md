# retellai-enterprise-sso

> Configure enterprise SSO and organization management for Retell AI team access

## Directory Structure

```
retellai-enterprise-sso/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for enterprise SSO configuration |
| examples/example.py | Python | Example SSO integration and team management scripts |

## Summary

**Category:** enterprise
**Target Audience:** Security architects, Identity engineers, Platform administrators
**Trigger Phrases:** `retell SSO`, `retell enterprise`, `retell team access`, `retell SAML`

### What This Skill Does

This skill configures enterprise-grade access control for Retell AI. It covers SSO integration with identity providers (Okta, Azure AD, Google Workspace), team role definitions and permission management, API key scoping per team or project, audit trail configuration for compliance, and automated provisioning/deprovisioning workflows.

### Technical Success Criteria

- SSO integration configured and tested
- Team roles defined with appropriate permissions
- API keys scoped to team boundaries
- Audit trail enabled for all access
- Automated provisioning working

### Business Success Criteria

- Enterprise security compliance achieved
- Centralized access control for voice AI
- Zero unauthorized access incidents, complete audit trail

## Related Skills

- retellai-security-basics - General security patterns
- retellai-compliance-recording - Recording access control
- retellai-multi-env-setup - Environment-based access
