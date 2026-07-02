---
name: openrouter-team-setup
description: 'Configure OpenRouter for multi-user teams with per-user keys, budget
  controls, and usage attribution. Triggers: ''openrouter team'', ''openrouter multi-user'',
  ''openrouter organization'', ''team api keys openrouter''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- team
- organization
- governance
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Team Setup

## Overview

OpenRouter supports team usage through per-user API keys with individual credit limits, management keys for programmatic key provisioning, and usage attribution via headers. This skill covers key provisioning, per-user budgets, usage tracking, and governance policies for multi-user deployments.

## Prerequisites

- A management key (`sk-or-v1-...`) with provisioning rights exported as `OPENROUTER_MGMT_KEY` — created separately at openrouter.ai/keys; it can create/list/delete API keys but cannot call completions
- A regular OpenRouter API key exported as `OPENROUTER_API_KEY` for the shared-key attribution pattern — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK and `requests`; `sqlite3` (stdlib) backs the per-user budget database
- `curl` and `jq` for the Team Key Dashboard Script

## Instructions

1. Create a management key at openrouter.ai/keys and export it as `OPENROUTER_MGMT_KEY`.
2. Provision one key per team member via Key Provisioning via Management API — `create_team_key(name, credit_limit)` posts to `/api/v1/keys`; record the one-time `key` value and keep the `key_hash` for later listing/revocation.
3. Alternatively, keep a single shared key and attribute usage per user with the Shared Key with User Attribution pattern (`X-Title: my-app:{user_id}` header shows each user in the dashboard).
4. Enforce spend locally with Per-User Budget Enforcement — initialize the `user_usage` / `user_budgets` sqlite tables, call `check_user_budget` before each request and `record_user_usage` after.
5. Gate expensive models per tier with the Model Governance allowlists (`enforce_model_policy` downgrades disallowed requests).
6. Monitor continuously: run the Team Key Dashboard Script (curl + jq against `/api/v1/keys`) and generate the weekly Team Usage Report from the sqlite DB.
7. Revoke keys for departed members with `delete_team_key(key_hash)` (`DELETE /api/v1/keys/{hash}`).

## Key Provisioning via Management API

```python
import os, requests

MGMT_KEY = os.environ["OPENROUTER_MGMT_KEY"]  # Management key (cannot call completions)

def create_team_key(name: str, credit_limit: float = 25.0) -> dict:
    """Create a new API key for a team member."""
    resp = requests.post(
        "https://openrouter.ai/api/v1/keys",
        headers={"Authorization": f"Bearer {MGMT_KEY}"},
        json={"name": name, "limit": credit_limit},
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    return {
        "key": data["key"],       # sk-or-v1-... (shown once)
        "hash": data["key_hash"], # For later identification
        "name": name,
        "limit": credit_limit,
    }

def list_team_keys() -> list[dict]:
    """List all keys with usage and limits."""
    resp = requests.get(
        "https://openrouter.ai/api/v1/keys",
        headers={"Authorization": f"Bearer {MGMT_KEY}"},
    )
    return [
        {
            "name": k.get("name"),
            "hash": k.get("key_hash"),
            "usage": k.get("usage", 0),
            "limit": k.get("limit"),
            "is_free_tier": k.get("is_free_tier", False),
        }
        for k in resp.json().get("data", [])
    ]

def delete_team_key(key_hash: str):
    """Revoke a team member's key."""
    resp = requests.delete(
        f"https://openrouter.ai/api/v1/keys/{key_hash}",
        headers={"Authorization": f"Bearer {MGMT_KEY}"},
    )
    resp.raise_for_status()

# Provision keys for the team
for member in ["alice-backend", "bob-frontend", "carol-ml"]:
    key_info = create_team_key(member, credit_limit=50.0)
    print(f"Created key for {member}: {key_info['key'][:20]}...")
```

## Shared Key with User Attribution

```python
from openai import OpenAI

# Alternative: single shared key with user identification via headers
def get_client_for_user(user_id: str) -> OpenAI:
    """Create a client that attributes usage to a specific user."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={
            "HTTP-Referer": "https://my-app.com",
            "X-Title": f"my-app:{user_id}",  # User shows in dashboard
        },
    )

# Each user's requests appear under their X-Title in the dashboard
alice_client = get_client_for_user("alice")
response = alice_client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
```

## Per-User Budget Enforcement

```python
import sqlite3, time

def init_team_db(db_path: str = "team_usage.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_usage (
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            total_cost REAL DEFAULT 0,
            request_count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_budgets (
            user_id TEXT PRIMARY KEY,
            daily_limit REAL NOT NULL,
            model_allowlist TEXT  -- JSON array of allowed model IDs
        )
    """)
    conn.commit()
    return conn

def check_user_budget(conn, user_id: str) -> bool:
    """Check if user is within their daily budget."""
    today = time.strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT u.total_cost, b.daily_limit FROM user_usage u "
        "JOIN user_budgets b ON u.user_id = b.user_id "
        "WHERE u.user_id = ? AND u.date = ?",
        (user_id, today),
    ).fetchone()

    if not row:
        return True  # No usage yet today
    return row[0] < row[1]

def record_user_usage(conn, user_id: str, cost: float):
    """Record a request's cost for a user."""
    today = time.strftime("%Y-%m-%d")
    conn.execute(
        """INSERT INTO user_usage (user_id, date, total_cost, request_count)
           VALUES (?, ?, ?, 1)
           ON CONFLICT(user_id, date) DO UPDATE SET
           total_cost = total_cost + ?, request_count = request_count + 1""",
        (user_id, today, cost, cost),
    )
    conn.commit()
```

## Team Usage Report

```python
def team_usage_report(conn) -> list[dict]:
    """Generate a team usage report for the current week."""
    rows = conn.execute("""
        SELECT u.user_id, SUM(u.total_cost) as weekly_cost,
               SUM(u.request_count) as requests,
               b.daily_limit
        FROM user_usage u
        JOIN user_budgets b ON u.user_id = b.user_id
        WHERE u.date >= date('now', '-7 days')
        GROUP BY u.user_id
        ORDER BY weekly_cost DESC
    """).fetchall()

    return [
        {
            "user": row[0],
            "weekly_cost": round(row[1], 4),
            "requests": row[2],
            "daily_limit": row[3],
        }
        for row in rows
    ]
```

## Team Key Dashboard Script

```bash
#!/bin/bash
# Show all team keys with usage

echo "=== OpenRouter Team Keys ==="
curl -s https://openrouter.ai/api/v1/keys \
  -H "Authorization: Bearer $OPENROUTER_MGMT_KEY" | \
  jq -r '.data[] | "\(.name)\t$\(.usage // 0 | tostring)\t/\t$\(.limit // "unlimited" | tostring)"' | \
  column -t -s $'\t'

echo ""
echo "=== Total Usage ==="
curl -s https://openrouter.ai/api/v1/keys \
  -H "Authorization: Bearer $OPENROUTER_MGMT_KEY" | \
  jq '.data | map(.usage // 0) | add | "Total spend: $\(.)"'
```

## Model Governance

```python
# Define which models each tier can use
MODEL_ALLOWLISTS = {
    "free": ["google/gemma-2-9b-it:free"],
    "basic": ["openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct"],
    "pro": ["openai/gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-3.5-sonnet"],
    "enterprise": None,  # None = all models allowed
}

def enforce_model_policy(user_tier: str, requested_model: str) -> str:
    """Enforce model allowlist based on user tier."""
    allowlist = MODEL_ALLOWLISTS.get(user_tier)
    if allowlist is None:
        return requested_model  # Enterprise: unrestricted
    if requested_model in allowlist:
        return requested_model
    # Downgrade to best allowed model
    return allowlist[-1]
```

## Output

- Per-member API keys (`sk-or-v1-...`, shown once at creation) plus `key_hash` records carrying name, usage, and credit limit
- A `team_usage.db` sqlite database with per-user daily `total_cost` and `request_count` rows plus per-user budgets and model allowlists
- A columnar key dashboard from the curl + jq script: key name, spend, and limit per row, plus a total-spend line
- A weekly team usage report list sorted by `weekly_cost`, one dict per user with requests and daily limit

## Examples

Provision keys for three team members with a $50 credit limit each:

```python
for member in ["alice-backend", "bob-frontend", "carol-ml"]:
    key_info = create_team_key(member, credit_limit=50.0)
    print(f"Created key for {member}: {key_info['key'][:20]}...")
# Created key for alice-backend: sk-or-v1-a1b2c3d4e5...
# Created key for bob-frontend: sk-or-v1-f6a7b8c9d0...
# Created key for carol-ml: sk-or-v1-e1f2a3b4c5...
```

Each key value is only returned once — store it securely and keep the hash for revocation. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Management key 403 | Using API key instead of management key | Management keys are separate -- create one at openrouter.ai/keys |
| User exceeds budget | No per-user limits set | Create individual keys with credit limits |
| Attribution missing | No X-Title header | Enforce header in shared client wrapper |
| Key sprawl | Too many keys to track | Implement key lifecycle management; revoke unused keys |

## Enterprise Considerations

- Use management keys for programmatic key provisioning -- they can create/list/delete API keys but cannot make completions
- Set per-key credit limits to prevent any single user from exhausting shared budget
- Use `X-Title` header with user identifiers for dashboard-level attribution
- Implement model allowlists per user tier to control access to expensive models
- Build weekly usage reports for cost visibility and anomaly detection
- Rotate team keys on a schedule; revoke keys for departed team members immediately

## References

- Examples | Errors
- [Key Provisioning](https://openrouter.ai/docs/guides/overview/auth/provisioning-api-keys) | [Auth API](https://openrouter.ai/docs/api/reference/authentication)
