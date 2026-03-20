---
name: lokalise-enterprise-rbac
description: |
  Configure Lokalise enterprise SSO, role-based access control, and team management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Lokalise.
  Trigger with phrases like "lokalise SSO", "lokalise RBAC",
  "lokalise enterprise", "lokalise roles", "lokalise permissions", "lokalise team".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(node:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Enterprise RBAC

## Overview

Manage fine-grained access to Lokalise translation projects using its built-in role hierarchy, language-level scoping, contributor groups, and organization-level SSO enforcement. Lokalise has four core roles — owner, admin, manager-level (via admin_rights), and contributor (translator/reviewer) — each configurable per project and per language.

## Prerequisites

- Lokalise Team or Enterprise plan (contributor groups and SSO require Team+)
- Owner or Admin role in the Lokalise organization
- `LOKALISE_API_TOKEN` environment variable set (admin-level token)
- `@lokalise/node-api` SDK or `curl` + `jq` for REST API access

## Instructions

### Step 1: Understand the Role Hierarchy

Lokalise uses a flat role model per project, controlled by three boolean flags on each contributor:

| Role | `is_admin` | `is_reviewer` | Can translate | Can review | Can manage keys | Can manage contributors |
|------|-----------|--------------|--------------|-----------|----------------|----------------------|
| **Admin** | `true` | `true` | Yes | Yes | Yes | Yes |
| **Manager** | `false` | `true` | Yes | Yes | Limited (via `admin_rights`) | No |
| **Reviewer** | `false` | `true` | Yes | Yes | No | No |
| **Translator** | `false` | `false` | Yes | No | No | No |

At the **team level**, users are either `admin` or `member`. Team admins can create projects and manage billing. Team members can only access projects they are explicitly added to.

### Step 2: Add Contributors with Language Scoping

```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Add a translator restricted to French and Spanish only
await lok.contributors().create(PROJECT_ID, [{
  email: 'translator@agency.com',
  fullname: 'Marie Dupont',
  is_admin: false,
  is_reviewer: false,
  languages: [
    { lang_iso: 'fr', is_writable: true },
    { lang_iso: 'es', is_writable: true },
  ],
}]);

// Add a reviewer who can review all languages but only translate German
await lok.contributors().create(PROJECT_ID, [{
  email: 'reviewer@company.com',
  fullname: 'Hans Mueller',
  is_admin: false,
  is_reviewer: true,
  languages: [
    { lang_iso: 'de', is_writable: true },
    { lang_iso: 'fr', is_writable: false },  // Can review but not edit
    { lang_iso: 'es', is_writable: false },
  ],
}]);
```

### Step 3: Manage Team-Level Users and Roles

```bash
set -euo pipefail
TEAM_ID="YOUR_TEAM_ID"

# List all team members with their roles
curl -s -X GET "https://api.lokalise.com/api2/teams/${TEAM_ID}/users" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq '.team_users[] | {user_id: .user_id, email: .email, role: .role}'

# Demote a user from admin to member
curl -s -X PUT "https://api.lokalise.com/api2/teams/${TEAM_ID}/users/USER_ID" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role": "member"}'
```

### Step 4: Create Contributor Groups for Bulk Management

Groups let you assign the same permissions to multiple people at once. When you add a user to a group, they inherit the group's language scope and role across all projects the group is assigned to.

```bash
set -euo pipefail
TEAM_ID="YOUR_TEAM_ID"

# Create a group for APAC translators
curl -s -X POST "https://api.lokalise.com/api2/teams/${TEAM_ID}/groups" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APAC Translators",
    "is_reviewer": false,
    "is_admin": false,
    "admin_rights": [],
    "languages": [
      {"lang_iso": "ja", "is_writable": true},
      {"lang_iso": "ko", "is_writable": true},
      {"lang_iso": "zh_CN", "is_writable": true}
    ]
  }'

# Add a member to the group
GROUP_ID=$(curl -s "https://api.lokalise.com/api2/teams/${TEAM_ID}/groups" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  | jq -r '.groups[] | select(.name == "APAC Translators") | .group_id')

curl -s -X PUT "https://api.lokalise.com/api2/teams/${TEAM_ID}/groups/${GROUP_ID}/members/add" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"users": [12345, 67890]}'

# Assign the group to specific projects
curl -s -X PUT "https://api.lokalise.com/api2/teams/${TEAM_ID}/groups/${GROUP_ID}/projects/add" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"projects": ["PROJECT_ID_1", "PROJECT_ID_2"]}'
```

### Step 5: Configure SSO (Enterprise Plan Only)

SSO is configured in the Lokalise dashboard, not via API. Map your IdP groups to Lokalise roles:

1. Navigate to **Organization Settings > Single Sign-On**
2. Select SAML 2.0 and enter your IdP metadata URL
3. Map IdP groups to Lokalise roles:
   - `Engineering-Localization` -> Admin
   - `Translators-EMEA` -> Contributor group "EMEA Translators"
   - `Product-Managers` -> Reviewer
4. Enable **Enforce SSO** to block password-based login for all org members
5. Set **Default Role** for new SSO users (recommend: member with no project access)

**ACS URL format:** `https://app.lokalise.com/sso/saml/YOUR_TEAM_ID/callback`

### Step 6: Audit Permissions Regularly

```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

async function auditPermissions() {
  const projects = await lok.projects().list({ limit: 100 });
  const report: Array<{project: string; issue: string; detail: string}> = [];

  for (const proj of projects.items) {
    const contributors = await lok.contributors().list({
      project_id: proj.project_id,
      limit: 500,
    });

    // Flag: too many admins
    const admins = contributors.items.filter(c => c.is_admin);
    if (admins.length > 3) {
      report.push({
        project: proj.name,
        issue: 'Excessive admins',
        detail: `${admins.length} admins: ${admins.map(a => a.email).join(', ')}`,
      });
    }

    // Flag: contributors with no language scope (can see all languages)
    const unscopedTranslators = contributors.items.filter(
      c => !c.is_admin && (!c.languages || c.languages.length === 0)
    );
    if (unscopedTranslators.length > 0) {
      report.push({
        project: proj.name,
        issue: 'Unscoped contributors',
        detail: `${unscopedTranslators.length} users can access all languages`,
      });
    }

    // Respect rate limit
    await new Promise(r => setTimeout(r, 200));
  }

  console.table(report);
  return report;
}

await auditPermissions();
```

### Step 7: Set Up Webhook for Access Change Notifications

```bash
set -euo pipefail
# Get notified when contributors are added or removed
curl -s -X POST "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.company.com/lokalise-audit",
    "events": [
      "project.contributor_added",
      "project.contributor_deleted",
      "project.contributor_added_to_language",
      "project.contributor_deleted_from_language"
    ]
  }'
```

## Output

- Contributors added with explicit language scoping (no unscoped access)
- Contributor groups created for bulk role management across projects
- Team-level roles configured (admin vs. member distinction)
- SSO configured with IdP group-to-role mapping (Enterprise)
- Audit script identifying over-privileged users and unscoped contributors
- Webhook configured for access change notifications

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on contributor create | Caller lacks Admin role on the project | Use an admin-level token or get elevated by an Owner |
| Translator sees all languages | No `languages` array set on contributor | Update contributor with explicit language scope array |
| SSO login loop | Mismatched ACS URL | Verify ACS URL matches `https://app.lokalise.com/sso/saml/TEAM_ID/callback` exactly |
| Cannot remove Owner | Last owner protection | Transfer ownership to another admin first |
| `400` on group create | `admin_rights` contains invalid values | Valid values: `activity`, `statistics`, `settings`, `manage_keys`, `manage_screenshots`, `manage_languages`, `manage_contributors` |
| Group members don't see project | Group not assigned to the project | Use the groups/projects/add endpoint to link them |

## Examples

### List All Contributors Across All Projects

```bash
set -euo pipefail
# Quick CSV export of all contributors and their roles
curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects?limit=100" \
  | jq -r '.projects[].project_id' \
  | while read -r pid; do
    curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
      "https://api.lokalise.com/api2/projects/${pid}/contributors?limit=500" \
      | jq -r --arg pid "$pid" '.contributors[] | [$pid, .email, (.is_admin|tostring), (.is_reviewer|tostring), (.languages|length|tostring)] | @csv'
    sleep 0.2
  done | sort -t, -k2
```

### Principle of Least Privilege Setup

For a typical project with 3 languages (en, fr, de):

```typescript
// Product team: admin access for key management
await lok.contributors().create(PROJECT_ID, [{
  email: 'pm@company.com', fullname: 'PM', is_admin: true, is_reviewer: true, languages: [],
}]);

// French translator: only French, translate only
await lok.contributors().create(PROJECT_ID, [{
  email: 'fr@agency.com', fullname: 'FR Translator', is_admin: false, is_reviewer: false,
  languages: [{ lang_iso: 'fr', is_writable: true }],
}]);

// German reviewer: German write + French read-only for reference
await lok.contributors().create(PROJECT_ID, [{
  email: 'de@agency.com', fullname: 'DE Reviewer', is_admin: false, is_reviewer: true,
  languages: [
    { lang_iso: 'de', is_writable: true },
    { lang_iso: 'fr', is_writable: false },
  ],
}]);
```

## Resources

- [Lokalise Contributors API](https://developers.lokalise.com/reference/list-all-contributors)
- [Team Users API](https://developers.lokalise.com/reference/list-team-users)
- [Contributor Groups API](https://developers.lokalise.com/reference/list-all-groups)
- [SSO Configuration Guide](https://docs.lokalise.com/en/articles/4866048-sso-saml)
- [Webhook Events Reference](https://developers.lokalise.com/reference/webhook-events)

## Next Steps

- After setting up permissions, run `lokalise-debug-bundle` to verify access scoping works as expected.
- For migration scenarios requiring bulk contributor setup, see `lokalise-migration-deep-dive`.
- Monitor access patterns over time with the audit script from Step 6.
