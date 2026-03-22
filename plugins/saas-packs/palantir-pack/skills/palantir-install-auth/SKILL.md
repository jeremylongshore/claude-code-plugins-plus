---
name: palantir-install-auth
description: |
  Install and configure Palantir Foundry SDK authentication with OAuth2 or token auth.
  Use when setting up a new Foundry integration, configuring API credentials,
  or initializing the foundry-platform-sdk in your project.
  Trigger with phrases like "install palantir", "setup palantir",
  "palantir auth", "configure palantir API key", "foundry SDK setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, authentication, setup]
compatible-with: claude-code, codex, openclaw
---

# Palantir Install & Auth

## Overview
Set up the Palantir Foundry Platform SDK (Python or TypeScript) and configure authentication using either bearer tokens for development or OAuth2 client credentials for production. Covers both the Platform SDK for direct API access and the OSDK for Ontology-based workflows.

## Prerequisites
- Python 3.9+ or Node.js 18+
- A Palantir Foundry enrollment with API access enabled
- A third-party application registered in Developer Console (for OAuth2)
- Your Foundry hostname (e.g., `mycompany.palantirfoundry.com`)

## Instructions

### Step 1: Install the SDK

**Python (Platform SDK):**
```bash
set -euo pipefail
pip install foundry-platform-sdk
python -c "import foundry; print(f'foundry-platform-sdk {foundry.__version__} installed')"
```

**Python (OSDK for Ontology access):**
```bash
set -euo pipefail
pip install palantir-sdk
python -c "import palantir; print('palantir-sdk installed')"
```

**TypeScript (OSDK):**
```bash
set -euo pipefail
npm install @osdk/client @osdk/oauth
npx tsc --version
```

### Step 2: Configure Environment Variables
```bash
# .env — never commit this file
FOUNDRY_HOSTNAME=mycompany.palantirfoundry.com

# Option A: Bearer token (development only)
FOUNDRY_TOKEN=eyJhbGciOiJS...

# Option B: OAuth2 client credentials (production)
FOUNDRY_CLIENT_ID=abc123
FOUNDRY_CLIENT_SECRET=secret456
```

### Step 3: Initialize with Bearer Token (Development)
```python
import os
import foundry

client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        token=os.environ["FOUNDRY_TOKEN"],
    ),
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

# Verify connection — list datasets
datasets = client.datasets.Dataset.list()
for ds in datasets:
    print(f"Dataset: {ds.rid}")
```

### Step 4: Initialize with OAuth2 (Production)
```python
import os
import foundry

auth = foundry.ConfidentialClientAuth(
    client_id=os.environ["FOUNDRY_CLIENT_ID"],
    client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
    hostname=os.environ["FOUNDRY_HOSTNAME"],
    scopes=["api:read-data", "api:write-data"],
)
auth.sign_in_as_service_user()

client = foundry.FoundryClient(
    auth=auth,
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

# Verify — fetch ontology metadata
ontologies = client.ontologies.Ontology.list()
for ont in ontologies:
    print(f"Ontology: {ont.api_name} (rid={ont.rid})")
```

### Step 5: TypeScript OSDK Setup
```typescript
import { createClient } from "@osdk/client";
import { createConfidentialOauthClient } from "@osdk/oauth";

const oauthClient = createConfidentialOauthClient(
  process.env.FOUNDRY_CLIENT_ID!,
  process.env.FOUNDRY_CLIENT_SECRET!,
  `https://${process.env.FOUNDRY_HOSTNAME}/multipass/api/oauth2/token`,
);

const client = createClient(
  `https://${process.env.FOUNDRY_HOSTNAME}`,
  "<your-ontology-rid>",
  oauthClient,
);
```

### Step 6: Generate Credentials via Developer Console
```text
1. Navigate to https://<hostname>/workspace/developer-console
2. Create a new application > select "Server application"
3. Grant scopes: api:read-data, api:write-data, api:ontology-read
4. Copy client_id and client_secret
5. For quick testing: generate a personal access token under Settings > Tokens
```

## Output
- SDK installed and importable (`foundry-platform-sdk` or `@osdk/client`)
- Environment variables configured for your Foundry enrollment
- Authenticated client verified against the Foundry API
- Ontology or dataset listing confirms read access

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Token expired or invalid | Regenerate token in Developer Console |
| `403 Forbidden` | Insufficient scopes | Add required scopes: `api:read-data` |
| `ConnectionError` | Wrong hostname | Verify `FOUNDRY_HOSTNAME` has no `https://` prefix |
| `ModuleNotFoundError: foundry` | SDK not installed | `pip install foundry-platform-sdk` (full name) |
| `SSL certificate verify failed` | Corporate proxy/VPN | Set `REQUESTS_CA_BUNDLE` env var |

## Examples

### SDK Comparison
| SDK | Package | Use Case |
|-----|---------|----------|
| Platform SDK | `foundry-platform-sdk` | Direct REST: datasets, branches, files, builds |
| Python OSDK | `palantir-sdk` | Ontology objects, actions, queries, links |
| TypeScript OSDK | `@osdk/client` | Frontend/Node.js Ontology access |

## Resources
- [Foundry API Getting Started](https://www.palantir.com/docs/foundry/api/general/overview/getting-started)
- [Authentication Guide](https://www.palantir.com/docs/foundry/api/general/overview/authentication)
- [Python SDK GitHub](https://github.com/palantir/foundry-platform-python)
- [OSDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)

## Next Steps
Proceed to `palantir-hello-world` for your first Ontology query, or `palantir-local-dev-loop` for development workflow.
