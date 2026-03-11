# Granola Enterprise RBAC - Implementation Details

## Role Definitions

### Organization Owner
```yaml
Role: Organization Owner
Level: Super Admin
Scope: Entire organization
Permissions: billing(full), org_settings(full), workspace_management(full), user_management(full), data_export(full), audit_logs(read), integrations(full), sso_configuration(full)
Limits: max_per_org 1-3, cannot be removed by other admins
```

### Organization Admin
```yaml
Role: Organization Admin
Permissions: billing(read), org_settings(read_write), workspace_management(full), user_management(full), data_export(full), audit_logs(read), integrations(full), sso_configuration(read)
```

### Workspace Admin
```yaml
Role: Workspace Admin
Scope: Assigned workspace(s)
Permissions: workspace_settings(full), member_management(full), templates(full), integrations(workspace_only), data_export(workspace_only), sharing_controls(full)
```

### Team Lead / Member / Viewer / Guest
```yaml
Team Lead: team_members(manage), templates(create_edit), notes(team_visibility), sharing(within_org)
Member: notes(create_edit_own), sharing(as_configured), templates(use), export(own_notes)
Viewer: notes(read_shared), read_only
Guest: notes(read_specific), time_limited, requires explicit invite
```

## Permission Matrices

### Note Permissions
| Action | Owner | Admin | Lead | Member | Viewer | Guest |
|--------|-------|-------|------|--------|--------|-------|
| Create | Yes | Yes | Yes | Yes | No | No |
| Edit Own | Yes | Yes | Yes | Yes | No | No |
| Edit Others | Yes | Yes | Team | No | No | No |
| Delete Others | Yes | Yes | No | No | No | No |
| View All | Yes | Yes | Team | Shared | Shared | Specific |

### Admin Permissions
| Action | Org Owner | Org Admin | WS Admin | Lead | Member |
|--------|-----------|-----------|----------|------|--------|
| Manage Billing | Yes | View | No | No | No |
| SSO Config | Yes | View | No | No | No |
| Create/Delete Workspace | Yes | Yes | No | No | No |
| Manage Users | Yes | Yes | WS Only | Team | No |
| View Audit Logs | Yes | Yes | WS Only | No | No |

## SSO Group Mapping

```yaml
SSO Provider: Okta

Group Mappings:
  "Granola-Owners": { role: organization_owner, workspaces: all }
  "Granola-Admins": { role: organization_admin, workspaces: all }
  "Engineering-Team": { role: member, workspaces: [engineering] }
  "Engineering-Leads": { role: workspace_admin, workspaces: [engineering] }
  "Sales-Team": { role: member, workspaces: [sales] }
  "External-Partners": { role: guest, workspaces: [partner-collab] }
```

## JIT Provisioning
```yaml
Settings:
  jit_provisioning: enabled
  default_role: member
  default_workspace: general
  require_email_domain: "@company.com"

Process:
  1. User signs in via SSO
  2. Account created automatically
  3. Groups evaluated -> role assigned
  4. Access granted immediately
```

## Access Policies

### Sharing Policy
```yaml
Internal Sharing: { default: enabled, team_sharing: automatic, cross_workspace: admin_approval }
External Sharing: { enabled: true, require_approval: workspace_admin, link_expiration: 30_days }
Public Links: { enabled: false }
```

### Data Access by Workspace
```yaml
Corporate: { visibility: owners_only, download: disabled, external: prohibited }
Engineering: { visibility: workspace, download: enabled, external: with_approval }
Sales: { visibility: workspace, download: enabled, external: enabled, crm_sync: automatic }
```

## Audit & Compliance

### Logged Actions
Role assigned/removed, permission changed, workspace access granted/revoked, guest invited/expired.

### Quarterly Access Review
- [ ] Export user role report
- [ ] Review admin access
- [ ] Check guest accounts
- [ ] Verify workspace assignments
- [ ] Remove inactive users
- [ ] Update role mappings

## Custom Roles (Enterprise)
```yaml
Role: Content Manager
Base: Member
Scope: Marketing Workspace
Additional: templates(create_edit_delete), shared_notes(edit_all), external_sharing(enabled)
Restrictions: cannot delete_others_notes, cannot manage_users
```

## User Lifecycle
- **Onboarding:** Create via SSO/JIT, assign default role, add to workspaces, provide training
- **Role Change:** Request from manager, approve by workspace admin, update role, verify access
- **Offboarding:** Triggered by HR, disable account, revoke access, transfer note ownership, archive after 30 days
