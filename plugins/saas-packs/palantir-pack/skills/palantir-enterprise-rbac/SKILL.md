---
name: palantir-enterprise-rbac
description: |
  Configure Palantir Foundry enterprise access control with project roles, markings, and service users.
  Use when implementing role-based access, configuring project permissions,
  or setting up service user accounts for Foundry integrations.
  Trigger with phrases like "palantir RBAC", "foundry roles",
  "palantir permissions", "foundry access control", "foundry service user".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, rbac, enterprise, security]
compatible-with: claude-code, codex, openclaw
---

# Palantir Enterprise RBAC

## Overview
Configure enterprise-grade access control in Foundry: project roles (Viewer/Editor/Owner), organization-level groups, service user accounts for integrations, and marking-based data classification.

## Prerequisites
- Foundry enrollment with admin access
- Understanding of Foundry project structure
- Familiarity with `palantir-security-basics`

## Instructions

### Step 1: Project Role Hierarchy
| Role | Permissions | Use Case |
|------|------------|----------|
| Viewer | Read datasets, view Ontology objects | Analysts, stakeholders |
| Editor | Read/write datasets, run builds | Data engineers, developers |
| Owner | Full control, manage members, configure | Project leads, admins |

### Step 2: Create Service Users for Integrations
```text
Developer Console > Applications > New Application:
1. Name: "order-sync-service" (descriptive of function)
2. Type: Server application (client credentials flow)
3. Scopes: api:read-data, api:ontology-read (minimum needed)
4. Project access: Add as Editor on specific projects only

Result: client_id + client_secret (store in secrets manager)
```

### Step 3: Scope Matrix by Application
```python
# Define per-application scopes
APP_SCOPES = {
    "dashboard-reader": ["api:read-data", "api:ontology-read"],
    "data-sync-service": ["api:read-data", "api:write-data"],
    "admin-tool": ["api:read-data", "api:write-data", "api:ontology-read", "api:ontology-write"],
}

def create_client_for_app(app_name: str) -> foundry.FoundryClient:
    scopes = APP_SCOPES[app_name]
    auth = foundry.ConfidentialClientAuth(
        client_id=os.environ[f"{app_name.upper().replace('-','_')}_CLIENT_ID"],
        client_secret=os.environ[f"{app_name.upper().replace('-','_')}_CLIENT_SECRET"],
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        scopes=scopes,
    )
    auth.sign_in_as_service_user()
    return foundry.FoundryClient(auth=auth, hostname=os.environ["FOUNDRY_HOSTNAME"])
```

### Step 4: Group-Based Access Control
```text
Organization Groups (manage in Foundry Admin):
├── data-engineering        → Editor on pipeline projects
├── data-science            → Viewer on pipeline, Editor on ML projects
├── business-analysts       → Viewer on analytics projects
├── external-partners       → Viewer on shared datasets only
└── platform-admins         → Owner on all projects

Principle: Users inherit access from groups.
Never assign project roles to individual users.
```

### Step 5: Audit Access Patterns
```python
def audit_service_user_access(client):
    """Check what the current service user can actually access."""
    accessible = {"ontologies": [], "datasets": []}
    try:
        for ont in client.ontologies.Ontology.list():
            accessible["ontologies"].append(ont.api_name)
    except foundry.ApiError:
        pass
    print(f"Accessible ontologies: {accessible['ontologies']}")
    return accessible
```

## Output
- Project roles assigned via groups (not individual users)
- Service users with minimum viable scopes per application
- Marking-based data classification enforced
- Access audit capability

## Error Handling
| Access Issue | Symptom | Fix |
|-------------|---------|-----|
| 403 on dataset read | Not a project member | Add user/group as Viewer |
| 403 on Ontology | Missing scope | Add `api:ontology-read` to app |
| Cannot see marked columns | Missing marking access | Grant marking to group |
| Service user sees everything | Over-scoped | Reduce to minimum scopes |

## Resources
- [Foundry Authentication](https://www.palantir.com/docs/foundry/api/general/overview/authentication)
- [Developer Console](https://www.palantir.com/docs/foundry/ontology-sdk/create-a-new-osdk)

## Next Steps
For incident response, see `palantir-incident-runbook`.
