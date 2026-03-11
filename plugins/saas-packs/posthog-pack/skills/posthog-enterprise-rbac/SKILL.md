---
name: posthog-enterprise-rbac
description: |
  Configure PostHog enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for PostHog.
  Trigger with phrases like "posthog SSO", "posthog RBAC",
  "posthog enterprise", "posthog roles", "posthog permissions", "posthog SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Enterprise RBAC

## Overview
Control access to PostHog analytics data, feature flags, and experiments using its organization and project-level permission model. PostHog has three hierarchy levels: Organization > Project > Resource.

## Prerequisites
- PostHog Cloud or self-hosted with Enterprise license
- Organization admin role
- Multiple projects configured for environment separation (prod, staging)

## Instructions

### Step 1: Set Up Project-Level Access
```bash
set -euo pipefail
# Create separate projects for prod and staging environments
curl -X POST https://app.posthog.com/api/organizations/ORG_ID/projects/ \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -d '{"name": "Production", "access_control": true}'

# Restrict team members to specific projects
curl -X POST https://app.posthog.com/api/projects/PROJECT_ID/members/ \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -d '{"user_id": "USER_ID", "level": 1}'
# Levels: 1=Member, 8=Admin
```

### Step 2: Configure Feature Flag Permissions
```yaml
# Feature flag access matrix
feature_flags:
  production_project:
    who_can_create: [admin, senior_engineer]
    who_can_edit: [admin, senior_engineer, engineer]
    who_can_delete: [admin]
    require_description: true
    require_rollout_review: true  # Two-person rule for >50% rollout
  staging_project:
    who_can_create: [admin, member]
    who_can_edit: [admin, member]
    who_can_delete: [admin, member]
```

### Step 3: Set Up SSO (Enterprise Only)
In PostHog Organization Settings > Authentication:
- Enable SAML 2.0 with your IdP
- Set "Enforce SSO" to require all members to authenticate via IdP
- Map IdP groups to PostHog organization roles
- Configure automatic provisioning for new IdP users

### Step 4: Create Scoped API Keys
```bash
set -euo pipefail
# Read-only key for the BI dashboard (no write access)
curl -X POST https://app.posthog.com/api/personal_api_keys/ \
  -H "Authorization: Bearer $POSTHOG_ADMIN_KEY" \
  -d '{"label": "bi-dashboard-readonly", "scopes": ["event:read", "insight:read", "dashboard:read"]}'

# Key for the feature flag service (flags only)
curl -X POST https://app.posthog.com/api/personal_api_keys/ \
  -H "Authorization: Bearer $POSTHOG_ADMIN_KEY" \
  -d '{"label": "feature-flag-service", "scopes": ["feature_flag:read", "feature_flag:write"]}'
```

### Step 5: Audit Access and Changes
```bash
set -euo pipefail
# Query the activity log for permission changes
curl "https://app.posthog.com/api/projects/PROJECT_ID/activity_log/?scope=Organization" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
  jq '.results[] | select(.activity | contains("member")) | {user: .user.email, activity, created_at}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on feature flag endpoint | Key missing `feature_flag` scope | Create key with appropriate scopes |
| Member can see prod data | Project access not restricted | Remove from prod project, add to staging only |
| SSO bypass possible | SSO not enforced | Enable "Enforce SSO" in org settings |
| Activity log gaps | Self-hosted log rotation | Increase retention in `posthog-config` |

## Examples

**Basic usage**: Apply posthog enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize posthog enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official PostHog documentation
- Community best practices and patterns
- Related skills in this plugin pack