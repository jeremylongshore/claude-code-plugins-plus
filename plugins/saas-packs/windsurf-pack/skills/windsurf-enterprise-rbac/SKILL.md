---
name: windsurf-enterprise-rbac
description: |
  Configure Windsurf enterprise SSO, RBAC, and organization-level controls.
  Use when implementing SSO/SAML, configuring role-based seat management,
  or setting up organization-wide Windsurf policies.
  Trigger with phrases like "windsurf SSO", "windsurf RBAC",
  "windsurf enterprise", "windsurf admin", "windsurf SAML", "windsurf team management".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, enterprise, sso, rbac, admin]

---
# Windsurf Enterprise RBAC

## Overview
Manage enterprise Windsurf deployment: SSO/SAML configuration, role-based seat management, organization-wide AI policies, and admin portal controls. Covers Teams and Enterprise plan features.

## Prerequisites
- Windsurf Teams ($30/user/mo) or Enterprise (custom pricing) plan
- Organization admin access at windsurf.com/dashboard
- Identity provider for SSO (Enterprise only): Okta, Entra ID, Google Workspace

## Instructions

### Step 1: Configure SSO / SAML (Enterprise Only)

Navigate to Admin Dashboard > Security > SSO:

```yaml
# SSO Configuration Steps
sso_setup:
  1_choose_idp:
    supported: ["Okta", "Microsoft Entra ID", "Google Workspace", "Any SAML 2.0 IdP"]

  2_configure_saml:
    entity_id: "https://windsurf.com/saml/your-org-id"
    acs_url: "https://windsurf.com/saml/callback"
    # Get these from Admin Dashboard > SSO > SAML Configuration

  3_idp_settings:
    # Configure in your IdP:
    sign_on_url: "https://windsurf.com/saml/login/your-org-id"
    audience_uri: "https://windsurf.com/saml/your-org-id"
    name_id_format: "emailAddress"
    attribute_statements:
      email: "user.email"
      firstName: "user.firstName"
      lastName: "user.lastName"

  4_enforce:
    enforce_sso: true  # Block password login after SSO is verified
    auto_provision: true  # New IdP users get Windsurf seats automatically
    domain_restriction: ["yourcompany.com"]  # Only allow company emails
```

### Step 2: Configure Roles and Permissions

```yaml
# Windsurf RBAC Model
roles:
  owner:
    description: "Organization owner — full control"
    permissions:
      - Manage billing and subscription
      - Add/remove admins
      - Configure SSO
      - View all analytics
      - Manage all seats

  admin:
    description: "Team administrator"
    permissions:
      - Add/remove members
      - Assign seat tiers (Pro, Free)
      - View team analytics
      - Configure org-wide settings
      - Manage MCP server allowlist

  member:
    description: "Standard developer"
    permissions:
      - Use assigned AI features
      - Configure personal settings
      - Create workspace rules
      - Cannot view team analytics

# Assign roles via Admin Dashboard > Members > Edit Role
```

### Step 3: Organization-Wide AI Policies

```yaml
# Admin Dashboard > Settings > AI Policies
org_policies:
  # Control which AI models are available
  allowed_models:
    - "swe-1"
    - "swe-1-lite"
    - "claude-sonnet"
    # Disable models not approved by security team

  # Terminal command execution controls
  cascade_terminal:
    max_execution_level: "normal"  # Options: turbo, normal, manual
    global_deny_list:
      - "rm -rf"
      - "sudo"
      - "curl | bash"
      - "DROP TABLE"
      - "format"

  # Data controls
  data_policies:
    telemetry: "off"                      # No telemetry for enterprise
    data_retention: "zero"                 # Zero-data retention
    code_context_sharing: "workspace_only" # AI sees only current workspace

  # Feature controls
  feature_flags:
    previews_enabled: true
    mcp_enabled: true
    workflows_enabled: true
    auto_deploy_enabled: false  # Disable direct deployment from IDE
```

### Step 4: Seat Management Workflow

```yaml
# Seat lifecycle management
seat_management:
  onboarding:
    1. "Admin invites user via Admin Dashboard > Members > Invite"
    2. "User receives email with SSO login link"
    3. "SSO authenticates user with company IdP"
    4. "User gets assigned tier (Pro/Free) based on role"
    5. "User opens project — .windsurfrules provides context"

  offboarding:
    1. "Disable user in IdP (SSO will auto-block)"
    2. "Remove seat in Admin Dashboard > Members"
    3. "Seat becomes available for reassignment"
    4. "User's local memories/config remain on their machine"

  tier_changes:
    upgrade: "Admin Dashboard > Members > Select user > Change to Pro"
    downgrade: "Admin Dashboard > Members > Select user > Change to Free"
    note: "Downgraded users keep Supercomplete, lose Cascade Write mode"
```

### Step 5: Audit and Compliance

```yaml
# Admin Dashboard > Analytics > Audit
audit_capabilities:
  available:
    - User login events (SSO audit trail)
    - Credit usage per user per day
    - Feature usage patterns
    - Seat assignment changes
    - Admin actions

  exportable:
    - CSV export of member usage
    - API access for SIEM integration (Enterprise)

  compliance_certifications:
    - SOC 2 Type II
    - FedRAMP High
    - HIPAA BAA (on request)
    - GDPR compliant
```

### Step 6: Service Keys for API Access (Enterprise)

```yaml
# For programmatic access to admin APIs
service_keys:
  purpose: "CI/CD integration, usage reporting, automated provisioning"
  create: "Admin Dashboard > Settings > Service Keys > Create"
  scopes:
    - "admin:read" — read analytics and member data
    - "admin:write" — manage members and settings
    - "usage:read" — read usage metrics
  rotation: "Rotate every 90 days, revoke immediately on compromise"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login fails | SAML certificate expired | Update certificate in IdP and Windsurf |
| User can't access Cascade | No Pro seat assigned | Assign Pro tier in Admin Dashboard |
| Admin can't see analytics | Wrong role | Upgrade to admin role in Dashboard |
| New user auto-provisioned to wrong tier | Default tier not set | Configure default seat tier in Settings |
| Service key rejected | Expired or wrong scope | Generate new key with correct scopes |

## Examples

### Quick Admin Dashboard Tasks
```
Add user: Admin Dashboard > Members > Invite > email@company.com
Remove user: Members > Select > Remove from organization
Change tier: Members > Select > Change Plan > Pro/Free
View usage: Analytics > Overview (or per-member view)
```

### Team Structure Example
```yaml
engineering_org:
  platform_team:
    seats: 8
    tier: Pro
    admins: ["tech-lead@company.com"]

  frontend_team:
    seats: 6
    tier: Pro
    admins: ["frontend-lead@company.com"]

  design_team:
    seats: 3
    tier: Free  # Mainly CSS, limited AI use

  contractors:
    seats: 4
    tier: Free
    note: "Temporary, upgrade to Pro if AI use increases"
```

## Resources
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)
- [Windsurf Enterprise](https://windsurf.com/enterprise)
- [Windsurf Security](https://windsurf.com/security)

## Next Steps
For migration strategies, see `windsurf-migration-deep-dive`.
