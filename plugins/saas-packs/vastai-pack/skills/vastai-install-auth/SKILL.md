---
name: vastai-install-auth
description: |
  Install and configure Vast.ai CLI and REST API authentication.
  Use when setting up a new Vast.ai integration, configuring API keys,
  or initializing Vast.ai GPU cloud access in your project.
  Trigger with phrases like "install vastai", "setup vastai",
  "vastai auth", "configure vastai API key", "vastai gpu setup".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(vastai:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, authentication]

---
# Vast.ai Install & Auth

## Overview
Set up the Vast.ai CLI and REST API access for renting GPU compute instances. Vast.ai is a marketplace where individual hosts and data centers list GPU machines at prices significantly below hyperscaler providers.

## Prerequisites
- Python 3.8+
- Vast.ai account at https://cloud.vast.ai
- Credit card or credits loaded for GPU rental

## Instructions

### Step 1: Install the CLI
```bash
set -euo pipefail
pip install vastai
vastai --version
```

### Step 2: Get Your API Key
1. Log in at https://cloud.vast.ai
2. Navigate to **Account** > **API Keys** (or visit https://cloud.vast.ai/cli/)
3. Copy your API key (a long hexadecimal string)

### Step 3: Configure Authentication
```bash
# Save API key to ~/.vast_api_key
vastai set api-key YOUR_API_KEY_HERE

# Verify authentication
vastai show user
```

For programmatic use, set the environment variable:
```bash
export VASTAI_API_KEY="your-api-key-here"
echo 'VASTAI_API_KEY=your-api-key' >> .env
```

### Step 4: Verify with REST API
```bash
# Direct REST API call — base URL is cloud.vast.ai/api/v0
curl -s -H "Authorization: Bearer $VASTAI_API_KEY" \
  "https://cloud.vast.ai/api/v0/users/current" | jq '{id, username, balance}'
```

### Step 5: Python Client Setup
```python
# vastai_client.py
import os
import requests
from typing import Optional, Dict, Any, List

class VastClient:
    BASE_URL = "https://cloud.vast.ai/api/v0"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VASTAI_API_KEY")
        if not self.api_key:
            # Fall back to ~/.vast_api_key
            key_file = os.path.expanduser("~/.vast_api_key")
            if os.path.exists(key_file):
                self.api_key = open(key_file).read().strip()
        if not self.api_key:
            raise ValueError("No API key found. Run: vastai set api-key YOUR_KEY")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def search_offers(self, query: Dict[str, Any]) -> List[Dict]:
        return self._request("GET", "/bundles/", params={"q": str(query)})

    def create_instance(self, offer_id: int, image: str, disk_gb: float = 20,
                        onstart: str = "", env: Dict = None) -> Dict:
        body = {"client_id": "me", "image": image, "disk": disk_gb,
                "onstart": onstart, "env": env or {}}
        return self._request("PUT", f"/asks/{offer_id}/", json=body)

    def show_instances(self) -> List[Dict]:
        return self._request("GET", "/instances/")["instances"]

    def destroy_instance(self, instance_id: int) -> Dict:
        return self._request("DELETE", f"/instances/{instance_id}/")

# Quick verification
if __name__ == "__main__":
    client = VastClient()
    user = client._request("GET", "/users/current")
    print(f"Authenticated as: {user['username']}")
    print(f"Balance: ${user.get('balance', 0):.2f}")
```

### Step 6: Verify Connection
```bash
# CLI verification
vastai show user
vastai search offers 'num_gpus=1 gpu_name=RTX_4090' --limit 3

# Python verification
python vastai_client.py
```

## Output
- `vastai` CLI installed and authenticated
- API key saved to `~/.vast_api_key` and/or environment variable
- Python client wrapper with search, create, show, destroy methods
- Successful authentication verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid API key` | Wrong or expired key | Regenerate at cloud.vast.ai/cli/ |
| `403 Forbidden` | Insufficient balance | Add credits at cloud.vast.ai |
| `Connection refused` | Firewall blocking HTTPS | Allow outbound 443 to cloud.vast.ai |
| `Module not found: vastai` | pip install failed | Run `pip install --upgrade vastai` |
| `~/.vast_api_key not found` | CLI not configured | Run `vastai set api-key YOUR_KEY` |

## Resources
- [Vast.ai CLI Documentation](https://docs.vast.ai/cli/get-started)
- [REST API Reference](https://vast.ai/developers/api)
- [API Introduction](https://docs.vast.ai/api-reference/introduction)
- [GitHub: vast-cli](https://github.com/vast-ai/vast-cli)

## Next Steps
After successful auth, proceed to `vastai-hello-world` for your first GPU instance rental.

## Examples

**Quick CLI test**: Run `vastai search offers 'reliability > 0.99 num_gpus=1' --order 'dph_total'` to find the cheapest reliable single-GPU offers. Verify your key works before writing any code.

**REST API test**: Use curl with your Bearer token to hit `cloud.vast.ai/api/v0/users/current` and confirm your username and balance are returned correctly.
