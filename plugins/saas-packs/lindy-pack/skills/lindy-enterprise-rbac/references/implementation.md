# Lindy Enterprise RBAC -- Implementation Details

## Role-Based Access Control

Lindy's enterprise model has three access levels:

- **Owner**: Full access including billing, team management, and all agents
- **Admin**: Can create/modify/delete agents and manage team members
- **Member**: Can view and run agents they have been granted access to

## Advanced Patterns

### Access Control Matrix

```python
from enum import Enum

class Role(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class Action(Enum):
    CREATE_AGENT = "create_agent"
    MODIFY_AGENT = "modify_agent"
    DELETE_AGENT = "delete_agent"
    TRIGGER_AGENT = "trigger_agent"
    VIEW_RUNS = "view_runs"
    VIEW_AGENT = "view_agent"
    MANAGE_TEAM = "manage_team"

RBAC_MATRIX: dict[Role, set[Action]] = {
    Role.OWNER:  set(Action),
    Role.ADMIN:  {
        Action.CREATE_AGENT, Action.MODIFY_AGENT, Action.DELETE_AGENT,
        Action.TRIGGER_AGENT, Action.VIEW_RUNS, Action.VIEW_AGENT, Action.MANAGE_TEAM,
    },
    Role.MEMBER: {Action.TRIGGER_AGENT, Action.VIEW_RUNS, Action.VIEW_AGENT},
    Role.VIEWER: {Action.VIEW_AGENT},
}

def require_permission(user_role: Role, action: Action) -> None:
    if action not in RBAC_MATRIX.get(user_role, set()):
        raise PermissionError(
            f"Role '{user_role.value}' cannot perform '{action.value}'. "
            "Required: admin or owner."
        )

require_permission(Role.ADMIN, Action.CREATE_AGENT)   # OK
# require_permission(Role.VIEWER, Action.DELETE_AGENT)  # PermissionError
```

### Team API Key Management

```python
import os
import requests
from typing import Optional
from datetime import datetime, timedelta, timezone

LINDY_API_BASE = "https://api.lindy.ai/v1"

def create_team_api_key(team_name: str, role: str = "member",
                        expires_days: Optional[int] = 90) -> dict:
    admin_key = os.environ["LINDY_ADMIN_API_KEY"]
    payload = {"name": f"team-{team_name.lower().replace(' ', '-')}", "role": role}
    if expires_days:
        expiry = datetime.now(timezone.utc) + timedelta(days=expires_days)
        payload["expires_at"] = expiry.isoformat()

    resp = requests.post(
        f"{LINDY_API_BASE}/api-keys",
        headers={
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
        },
        json=payload, timeout=10,
    )
    resp.raise_for_status()
    key_data = resp.json()
    print(f"Created key for '{team_name}': {key_data['name']} (role: {role})")
    # IMPORTANT: Store key_data['key'] securely -- it won't be shown again
    return key_data


def revoke_api_key(key_id: str) -> None:
    resp = requests.delete(
        f"{LINDY_API_BASE}/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {os.environ['LINDY_ADMIN_API_KEY']}"},
        timeout=10,
    )
    resp.raise_for_status()
    print(f"Revoked: {key_id}")
```

## Troubleshooting

### Member Cannot Trigger an Agent

1. Verify the member's role in Lindy dashboard (Settings > Team)
2. Check if the agent has restricted access settings
3. Confirm the member accepted their team invitation
4. Verify the API key belongs to the correct member

### Admin Actions Returning 403

1. Confirm `LINDY_API_KEY` has admin or owner role
2. Check if the key has expired in Settings > API Keys
3. Verify you are accessing the correct workspace

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
