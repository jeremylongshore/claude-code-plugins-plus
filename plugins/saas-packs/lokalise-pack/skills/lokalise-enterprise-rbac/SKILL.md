---
name: lokalise-enterprise-rbac
description: |
  Configure Lokalise enterprise SSO, role-based access control, and team management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Lokalise.
  Trigger with phrases like "lokalise SSO", "lokalise RBAC",
  "lokalise enterprise", "lokalise roles", "lokalise permissions", "lokalise team".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Enterprise RBAC

## Overview
Manage fine-grained access to Lokalise translation projects using its built-in role hierarchy. Lokalise distinguishes between organization-level roles (Owner, Admin, Biller) and project-level contributor roles (Manager, Developer, Translator, Reviewer) with optional language-pair restrictions, making it possible to give a French translator write access only to `fr` keys while locking them out of `de` content.

## Prerequisites
- Lokalise Team or Enterprise plan
- Admin or Owner role in the Lokalise organization
- `@lokalise/node-api` SDK or direct REST API access

## Instructions

### Step 1: Assign Project Contributors with Language Scoping
```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Add a translator restricted to French and Spanish only
await lok.contributors().create('PROJECT_ID', [{
  email: 'translator@agency.com',
  fullname: 'Marie Dupont',
  is_admin: false,
  is_reviewer: false,
  languages: [
    { lang_iso: 'fr', is_writable: true },
    { lang_iso: 'es', is_writable: true },
  ],
}]);
```

### Step 2: Manage Team-Level Roles
```bash
# List team members and roles
curl -X GET "https://api.lokalise.com/api2/teams/TEAM_ID/users" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN"

# Change a user from admin to member
curl -X PUT "https://api.lokalise.com/api2/teams/TEAM_ID/users/USER_ID" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  -d '{"role": "member"}'
```

### Step 3: Configure SSO (Enterprise Only)
In Lokalise Organization Settings > SSO, configure SAML 2.0 with your IdP. Map IdP groups to Lokalise roles:
- `Eng-Localization` -> Admin
- `Translators-FR` -> Contributor with `fr` language scope
- `Product-Managers` -> Reviewer

Enable "Enforce SSO" to block password-based login for all org members.

### Step 4: Set Up Contributor Groups for Bulk Management
```bash
# Create a contributor group scoped to specific languages and projects
curl -X POST "https://api.lokalise.com/api2/teams/TEAM_ID/groups" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  -d '{
    "name": "APAC Translators",
    "is_reviewer": false,
    "is_admin": false,
    "admin_rights": [],
    "languages": [{"lang_iso": "ja", "is_writable": true}, {"lang_iso": "ko", "is_writable": true}]
  }'
```

### Step 5: Audit Access Regularly
```typescript
// List all contributors across projects and flag over-privileged users
const projects = await lok.projects().list();
for (const proj of projects.items) {
  const contributors = await lok.contributors().list({ project_id: proj.project_id });
  const admins = contributors.items.filter(c => c.is_admin);
  if (admins.length > 3) {
    console.warn(`Project ${proj.name}: ${admins.length} admins (review needed)`);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on contributor create | Caller lacks Admin role | Elevate to Admin or Owner |
| Translator sees all languages | No language scope set | Update contributor with explicit `languages` array |
| SSO login loop | Mismatched ACS URL | Verify callback URL matches IdP config exactly |
| Cannot remove Owner | Last owner protection | Transfer ownership before removal |

## Examples
```bash
# Bulk add translators from CSV (email,lang)
while IFS=, read -r email lang; do
  curl -s -X POST "https://api.lokalise.com/api2/projects/PROJECT_ID/contributors" \
    -H "X-Api-Token: $LOKALISE_API_TOKEN" \
    -d "[{\"email\":\"$email\",\"languages\":[{\"lang_iso\":\"$lang\",\"is_writable\":true}]}]"
done < translators.csv
```
