# Linear Common Errors -- Implementation Details

## Authentication and Authorization Errors

### 401 Unauthorized

Occurs when the Linear API key is missing, expired, or invalid.

```python
import os
import requests

LINEAR_API_BASE = "https://api.linear.app/graphql"

def get_linear_headers() -> dict:
    key = os.environ.get("LINEAR_API_KEY", "")
    if not key:
        raise RuntimeError("LINEAR_API_KEY not set")
    return {
        "Authorization": key,  # Linear uses bare key, not "Bearer key"
        "Content-Type": "application/json",
    }

def verify_auth() -> dict:
    """Verify Linear API credentials are working."""
    query = '{ viewer { id name email } }'
    resp = requests.post(
        LINEAR_API_BASE,
        headers=get_linear_headers(),
        json={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        for error in data["errors"]:
            if error.get("extensions", {}).get("code") == "AUTHENTICATION_ERROR":
                raise RuntimeError(f"[AUTH] {error['message']} -- Check LINEAR_API_KEY")
    return data.get("data", {}).get("viewer", {})


user = verify_auth()
print(f"Authenticated as: {user.get('name')} ({user.get('email')})")
```

## GraphQL Error Handling

Linear uses GraphQL, so errors appear in the response body even when HTTP is 200.

```python
def safe_linear_query(query: str, variables: dict | None = None) -> dict:
    """Execute a Linear GraphQL query with proper error handling."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(
        LINEAR_API_BASE,
        headers=get_linear_headers(),
        json=payload,
        timeout=15,
    )

    # Linear can return 200 with errors in the body
    if resp.status_code == 429:
        raise RuntimeError(
            f"[429] Rate limited. Retry-After: {resp.headers.get('Retry-After', 'unknown')}s"
        )
    resp.raise_for_status()

    data = resp.json()
    if "errors" in data:
        errors = data["errors"]
        # Handle common error types
        for error in errors:
            code = error.get("extensions", {}).get("code", "")
            if code == "AUTHENTICATION_ERROR":
                raise RuntimeError(f"Auth error: {error['message']}")
            elif code == "RATE_LIMITED":
                raise RuntimeError(f"Rate limited: {error['message']}")
            elif code == "ENTITY_NOT_FOUND":
                raise ValueError(f"Not found: {error['message']}")
        raise RuntimeError(f"GraphQL errors: {errors}")

    return data.get("data", {})
```

## Advanced Patterns

### Common Issue Diagnostics

```python
def diagnose_linear_integration() -> list[str]:
    """Run diagnostic checks on Linear integration."""
    issues = []

    try:
        user = verify_auth()
        if not user:
            issues.append("Authentication failed -- check LINEAR_API_KEY")
    except Exception as e:
        issues.append(f"Auth error: {e}")
        return issues  # Can't proceed without auth

    # Check team access
    try:
        data = safe_linear_query("{ teams { nodes { id name } } }")
        teams = data.get("teams", {}).get("nodes", [])
        if not teams:
            issues.append("No teams accessible -- verify API key has correct workspace access")
        else:
            print(f"[OK] Access to {len(teams)} teams")
    except Exception as e:
        issues.append(f"Team access error: {e}")

    return issues


for issue in diagnose_linear_integration():
    print(f"[ISSUE] {issue}")
```

## Troubleshooting

### Mutation Returns False Success

Linear mutations often return `{ success: false }` without throwing HTTP errors.
Always check the `success` field in mutation responses:

```python
CREATE_ISSUE_MUTATION = """
mutation CreateIssue($title: String!, $teamId: String!) {
  issueCreate(input: { title: $title, teamId: $teamId }) {
    success
    issue { id title url }
  }
}
"""

def create_issue(title: str, team_id: str) -> dict:
    data = safe_linear_query(CREATE_ISSUE_MUTATION, {"title": title, "teamId": team_id})
    result = data.get("issueCreate", {})
    if not result.get("success"):
        raise RuntimeError(f"Issue creation failed -- check team ID and permissions")
    return result.get("issue", {})
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
