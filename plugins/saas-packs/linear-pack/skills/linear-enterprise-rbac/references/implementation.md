# Linear Enterprise RBAC -- Implementation Reference

## Overview

Implement role-based access control for Linear integrations in enterprise environments,
including SSO, team-level permissions, API key rotation, and audit logging.

## Prerequisites

- Linear workspace admin access
- Enterprise plan (for SSO/SAML features)
- Python 3.9+

## Role Matrix

| Role | Create Issues | Comment | Triage | Admin APIs |
|------|--------------|---------|--------|-----------|
| Viewer | No | No | No | No |
| Member | Yes | Yes | No | No |
| Triage | Yes | Yes | Yes | No |
| Admin | Yes | Yes | Yes | Yes |

## Python RBAC Audit Manager

```python
import os
import json
import logging
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]

def graphql(query: str, variables: dict = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY,
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if "errors" in result:
        raise RuntimeError(f"GraphQL errors: {result['errors']}")
    return result["data"]

def list_workspace_members() -> list:
    query = """
    query {
      users(filter: { active: { eq: true } }) {
        nodes {
          id name email admin
          teamMemberships { nodes { team { id name } role } }
        }
      }
    }
    """
    return graphql(query)["users"]["nodes"]

def audit_member_roles() -> dict:
    """Produce a role audit report for all active workspace members."""
    members = list_workspace_members()
    report = {
        "total": len(members),
        "by_role": {},
        "admins": [],
        "multi_team": [],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    for m in members:
        memberships = m.get("teamMemberships", {}).get("nodes", [])
        role = "admin" if m["admin"] else (memberships[0]["role"] if memberships else "none")
        report["by_role"].setdefault(role, []).append(m["email"])
        if m["admin"]:
            report["admins"].append(m["email"])
        if len(memberships) > 1:
            report["multi_team"].append({
                "email": m["email"],
                "teams": [mb["team"]["name"] for mb in memberships],
            })

    return report

def enforce_least_privilege(allowed_admins: list) -> list:
    """Demote admins not in the allowed list. Returns list of demoted emails."""
    members = list_workspace_members()
    demoted = []

    mutation = """
    mutation UpdateUser($id: String!, $input: UpdateUserInput!) {
      userUpdate(id: $id, input: $input) { success }
    }
    """
    for m in members:
        if m["admin"] and m["email"] not in allowed_admins:
            graphql(mutation, {"id": m["id"], "input": {"admin": False}})
            demoted.append(m["email"])
            logger.warning("Demoted admin: %s", m["email"])

    return demoted

def rotate_team_key_record(team: str, secret_backend: str = "github") -> None:
    """Document key rotation event -- actual rotation is manual in Linear UI."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": "api_key_rotated",
        "team": team,
        "backend": secret_backend,
    }
    logger.info("RBAC_AUDIT %s", json.dumps(entry))

def create_audit_log_entry(event: str, actor: str, target: str, metadata: dict) -> None:
    """Write RBAC event to structured audit log."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "actor": actor,
        "target": target,
        **metadata,
    }
    logger.info("RBAC_AUDIT %s", json.dumps(entry))

def get_team_scope(team_id: str) -> dict:
    """Return members and configuration for a specific team."""
    query = """
    query Team($id: String!) {
      team(id: $id) {
        id name
        members { nodes { user { email } role } }
        labels { nodes { name color } }
        states { nodes { name type } }
      }
    }
    """
    return graphql(query, {"id": team_id})["team"]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=== Role Audit ===")
    report = audit_member_roles()
    print(json.dumps(report, indent=2))

    allowed_admins = ["cto@example.com", "platform-lead@example.com"]
    demoted = enforce_least_privilege(allowed_admins)
    if demoted:
        create_audit_log_entry("admin_demoted", "rbac-enforcer", str(demoted), {})
        print(f"Demoted {len(demoted)} unauthorized admins")
    else:
        print("No unauthorized admins found")
```

## API Key Rotation Script

```bash
#!/bin/bash
# Rotate Linear API keys for a service team

set -euo pipefail

TEAM="${1:?Usage: $0 <team-name>}"
NEW_KEY="${LINEAR_NEW_API_KEY:?Set LINEAR_NEW_API_KEY}"

echo "Rotating Linear API key for team: ${TEAM}"

# Update GitHub Actions secret
if command -v gh &>/dev/null; then
    gh secret set "LINEAR_API_KEY_${TEAM^^}" --body "${NEW_KEY}"
    echo "Updated GitHub secret: LINEAR_API_KEY_${TEAM^^}"
fi

# Update Kubernetes secret
if command -v kubectl &>/dev/null; then
    kubectl create secret generic linear-api \
        --from-literal="api-key=${NEW_KEY}" \
        --namespace="${TEAM}" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

# Restart affected deployments
kubectl rollout restart deployment/linear-sync-"${TEAM}" 2>/dev/null || true
echo "Key rotation complete for team: ${TEAM}"
```

## SSO Attribute Mapping (Okta / Azure AD)

```yaml
# SAML attribute mapping for Linear SSO
saml_attributes:
  email: "user.email"
  name: "user.displayName"
  groups: "user.groups"  # Maps to Linear teams

group_to_linear_team:
  "eng-backend": "TEAM_ID_BACKEND"
  "eng-frontend": "TEAM_ID_FRONTEND"
  "eng-platform": "TEAM_ID_PLATFORM"
  "product": "TEAM_ID_PRODUCT"
  "design": "TEAM_ID_DESIGN"

# Default role for new members provisioned via SSO
default_role: "member"
admin_group: "linear-admins"
```

## Resources

- [Linear API -- Users](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- Linear SAML SSO
- [Linear Teams](https://linear.app/docs/teams)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
