# vercel-enterprise-rbac

## Skill Scaffold

```
vercel-enterprise-rbac/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure enterprise SSO, role-based access control, organization management, and audit trails.
**Workflow:** Used during enterprise onboarding and when adding new roles or SSO providers.
**Relates to:** Extends vercel-data-handling security; leads to vercel-migration-deep-dive for major changes

## Summary

This skill covers enterprise-grade access control for Vercel. It defines role types (Admin, Developer, Viewer, Service) with permission mappings, SAML configuration for SSO with IdP group-to-role mapping, OAuth2/OIDC integration patterns, organization management with SSO enforcement and allowed domains, Express.js middleware for permission checking, and comprehensive audit trail logging. The goal is zero unauthorized access with complete visibility.
