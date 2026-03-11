---
name: databricks-install-auth
description: |
  Install and configure Databricks CLI and SDK authentication.
  Use when setting up a new Databricks integration, configuring tokens,
  or initializing Databricks in your project.
  Trigger with phrases like "install databricks", "setup databricks",
  "databricks auth", "configure databricks token", "databricks CLI".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Install & Auth

## Overview
Set up Databricks CLI and SDK with authentication credentials.

## Prerequisites
- Python 3.8+ with pip
- Databricks workspace URL (e.g., `https://adb-1234567890.1.azuredatabricks.net`)
- Personal Access Token or OAuth credentials
- Admin access for Unity Catalog setup

## Instructions

### Step 1: Install Databricks CLI and SDK
```bash
set -euo pipefail
# Install CLI v2 (recommended)
pip install databricks-cli

# Install Python SDK
pip install databricks-sdk

# Install dbx for local development
pip install dbx
```

### Step 2: Configure Authentication

#### Option A: Personal Access Token (Simplest)
```bash
# Interactive configuration
databricks configure --token

# Enter workspace URL: https://adb-1234567890.1.azuredatabricks.net
# Enter token: dapi1234567890abcdef...
```

#### Option B: Environment Variables
```bash
# Set environment variables
export DATABRICKS_HOST="https://adb-1234567890.1.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi1234567890abcdef..."

# Or create .env file
cat > .env << 'EOF'
DATABRICKS_HOST=https://adb-1234567890.1.azuredatabricks.net
DATABRICKS_TOKEN=dapi1234567890abcdef...
EOF
```

#### Option C: OAuth (Recommended for Production)
```bash
# Using OAuth U2M (user-to-machine)
databricks configure --oauth

# Using OAuth M2M (service principal)
export DATABRICKS_HOST="https://adb-1234567890.1.azuredatabricks.net"
export DATABRICKS_CLIENT_ID="your-client-id"
export DATABRICKS_CLIENT_SECRET="your-client-secret"
```

### Step 3: Configure Profiles (Multi-Workspace)
```ini
# ~/.databrickscfg
[DEFAULT]
host = https://adb-dev-1234567890.1.azuredatabricks.net
token = dapi_dev_token...

[staging]
host = https://adb-staging-1234567890.1.azuredatabricks.net
token = dapi_staging_token...

[production]
host = https://adb-prod-1234567890.1.azuredatabricks.net
token = dapi_prod_token...
```

### Step 4: Verify Connection
```bash
# Test CLI connection
databricks workspace list /

# Test with specific profile
databricks workspace list / --profile staging

# Test SDK connection
python -c "
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
print(f'Connected to: {w.config.host}')
print(f'Clusters: {len(list(w.clusters.list()))}')
"
```

## Output
- Databricks CLI installed and configured
- Python SDK installed
- Authentication credentials stored
- Connection verified to workspace

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid token` | Expired or incorrect token | Generate new PAT in User Settings |
| `Workspace not found` | Wrong host URL | Verify workspace URL format |
| `Permission denied` | Token lacks permissions | Request admin access or correct scopes |
| `Connection refused` | Network/firewall issue | Check VPN, firewall rules |
| `SSL certificate error` | Corporate proxy | Set `--insecure` or configure proxy |

## Examples

### Python SDK Initialization
```python
from databricks.sdk import WorkspaceClient

# Auto-detect from environment/config file
w = WorkspaceClient()

# Explicit configuration
w = WorkspaceClient(
    host="https://adb-1234567890.1.azuredatabricks.net",
    token="dapi1234567890abcdef..."
)

# With profile
w = WorkspaceClient(profile="production")
```

### Service Principal Authentication
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config

config = Config(
    host="https://adb-1234567890.1.azuredatabricks.net",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
w = WorkspaceClient(config=config)
```

### Azure AD Authentication
```python
from databricks.sdk import WorkspaceClient
from azure.identity import DefaultAzureCredential

# Uses Azure AD managed identity
w = WorkspaceClient(
    host="https://adb-1234567890.1.azuredatabricks.net",
    credentials_provider=DefaultAzureCredential()
)
```

## Resources
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Databricks SDK for Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- [Authentication Methods](https://docs.databricks.com/dev-tools/auth.html)
- [Personal Access Tokens](https://docs.databricks.com/dev-tools/auth.html#personal-access-tokens)

## Next Steps
After successful auth, proceed to `databricks-hello-world` for your first cluster and notebook.