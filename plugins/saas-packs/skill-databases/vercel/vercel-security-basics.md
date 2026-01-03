# vercel-security-basics

## Skill Scaffold

```
vercel-security-basics/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Apply security best practices for API keys, secrets rotation, least privilege access, and webhook signature verification.
**Workflow:** Applied during initial setup and periodically audited during security reviews.
**Relates to:** Extends vercel-install-auth with security; leads to vercel-enterprise-rbac for enterprise needs

## Summary

This skill covers essential security practices for Vercel integrations. It includes proper API key storage using environment variables, .gitignore patterns to prevent credential leakage, secret rotation procedures, least privilege scope selection per environment, webhook signature verification using HMAC-SHA256, and audit logging patterns. The security checklist ensures all bases are covered before production deployment.
