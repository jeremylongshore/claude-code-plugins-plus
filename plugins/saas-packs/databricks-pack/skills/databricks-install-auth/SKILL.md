---
name: databricks-install-auth
description: |
  Install and configure Databricks CLI and SDK authentication.
  Use when setting up a new Databricks integration, configuring tokens,
  or initializing Databricks in your project.
  Trigger with phrases like "install databricks", "setup databricks",
  "databricks auth", "configure databricks token", "databricks CLI".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(databricks:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, authentication]

---
# Databricks Install & Auth

## Overview
Set up Databricks CLI v2, Python SDK, and authentication. Covers Personal Access Tokens (legacy), OAuth U2M (interactive), and OAuth M2M (service principal for CI/CD). Databricks strongly recommends OAuth over PATs for production.

## Prerequisites
- Python 3.8+ with pip
- Databricks workspace URL (e.g., `https://adb-1234567890123456.7.azuredatabricks.net`)
- For PAT: User Settings > Developer > Access Tokens in workspace UI
- For OAuth M2M: Service principal with client ID and secret

## Instructions

### Step 1: Install Databricks CLI and Python SDK
```bash
set -euo pipefail

# Install CLI v2 (standalone binary — recommended)
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Verify CLI
databricks --version

# Install Python SDK
pip install databricks-sdk

# Install Databricks Connect for local Spark development
pip install databricks-connect==14.3.*
```

### Step 2: Configure Authentication

#### Option A: Personal Access Token (Quick Start)
Generate a PAT in workspace UI: User Settings > Developer > Access Tokens.

```bash
# Interactive setup — prompts for host and token
databricks configure --token

# Or set environment variables directly
export DATABRICKS_HOST="https://adb-1234567890123456.7.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi_your_token_here"
```

#### Option B: OAuth U2M (User-to-Machine — Interactive)
Opens browser for OAuth consent. Token auto-refreshes (1-hour lifetime).

```bash
# Interactive OAuth login
databricks auth login --host https://adb-1234567890123456.7.azuredatabricks.net

# Verify — prints current user
databricks current-user me
```

#### Option C: OAuth M2M (Service Principal — CI/CD)
Uses client credentials flow. No browser required. Create a service principal in Account Console > Service Principals, then generate an OAuth secret.

```bash
export DATABRICKS_HOST="https://adb-1234567890123456.7.azuredatabricks.net"
export DATABRICKS_CLIENT_ID="00000000-0000-0000-0000-000000000000"
export DATABRICKS_CLIENT_SECRET="dose00000000000000000000000000000000"

# Verify
databricks current-user me
```

### Step 3: Configure Profiles for Multi-Workspace
```ini
# ~/.databrickscfg — one section per workspace
[DEFAULT]
host  = https://adb-dev-workspace.7.azuredatabricks.net
token = dapi_dev_token_here

[staging]
host  = https://adb-staging-workspace.7.azuredatabricks.net
token = dapi_staging_token_here

[production]
host       = https://adb-prod-workspace.7.azuredatabricks.net
client_id  = 00000000-0000-0000-0000-000000000000
client_secret = dose_prod_secret_here
```

```bash
# Use a specific profile
databricks workspace list / --profile staging
```

### Step 4: Verify SDK Connection
```python
from databricks.sdk import WorkspaceClient

# Auto-detects from env vars or ~/.databrickscfg
w = WorkspaceClient()

me = w.current_user.me()
print(f"Authenticated as: {me.user_name}")
print(f"Workspace: {w.config.host}")
print(f"Auth type: {w.config.auth_type}")

# Quick smoke test — list clusters
clusters = list(w.clusters.list())
print(f"Clusters found: {len(clusters)}")
```

### Step 5: Service Principal Authentication (Python SDK)
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config

# Explicit M2M config for CI/CD scripts
config = Config(
    host="https://adb-1234567890123456.7.azuredatabricks.net",
    client_id="00000000-0000-0000-0000-000000000000",
    client_secret="dose00000000000000000000000000000000",
)
w = WorkspaceClient(config=config)

# Or use a named profile
w = WorkspaceClient(profile="production")
```

## Output
- Databricks CLI v2 installed and on PATH
- Python SDK (`databricks-sdk`) installed
- Authentication credentials stored in env vars or `~/.databrickscfg`
- Connection verified with `databricks current-user me`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_TOKEN` | Token expired or revoked | Generate a new PAT or re-run `databricks auth login` |
| `Could not resolve host` | Wrong workspace URL | Verify URL format: `https://adb-<id>.<region>.azuredatabricks.net` |
| `PERMISSION_DENIED` | Token lacks required entitlements | Ensure user/SP has workspace access in Account Console |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Corporate proxy intercepts TLS | Set `REQUESTS_CA_BUNDLE=/path/to/cert.pem` |
| `Connection refused` | VPN or firewall blocking | Check corporate firewall rules for workspace domain |
| `No matching profile` | Profile name typo in `~/.databrickscfg` | Run `databricks auth profiles` to list available profiles |

## Examples

### Account-Level Client (Multi-Workspace Management)
```python
from databricks.sdk import AccountClient

# Account-level operations (manage workspaces, users, billing)
a = AccountClient(
    host="https://accounts.cloud.databricks.com",
    account_id="00000000-0000-0000-0000-000000000000",
    client_id="sp-client-id",
    client_secret="sp-secret",
)

for ws in a.workspaces.list():
    print(f"{ws.workspace_name}: {ws.deployment_name}")
```

### Azure AD Managed Identity
```python
from databricks.sdk import WorkspaceClient

# Uses Azure Default Credential chain (works in Azure VMs, AKS, Functions)
w = WorkspaceClient(
    host="https://adb-1234567890123456.7.azuredatabricks.net",
    azure_workspace_resource_id="/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Databricks/workspaces/<ws>",
)
```

## Resources
- [Databricks Authentication](https://docs.databricks.com/aws/en/dev-tools/auth/)
- [OAuth M2M](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [Databricks SDK for Python](https://docs.databricks.com/aws/en/dev-tools/sdk-python)
- [CLI Authentication](https://docs.databricks.com/aws/en/dev-tools/cli/authentication)

## Next Steps
After successful auth, proceed to `databricks-hello-world` for your first cluster and notebook.
