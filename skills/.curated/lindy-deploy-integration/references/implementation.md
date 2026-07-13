# Lindy Deploy Integration -- Implementation Details

## CI/CD Pipeline Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-lindy-agents.yml
name: Deploy Lindy Agents
on:
  push:
    branches: [main]
    paths: ['lindy-agents/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy agents to production
        env:
          LINDY_API_KEY: ${{ secrets.LINDY_API_KEY }}
        run: python3 scripts/deploy-lindy-agents.py --config-dir lindy-agents/
```

### Deploy Script

```python
import os
import json
import sys
import requests
from pathlib import Path

LINDY_API_BASE = "https://api.lindy.ai/v1"
HEADERS = {
    "Authorization": f"Bearer {os.environ['LINDY_API_KEY']}",
    "Content-Type": "application/json",
}


def get_existing_agents() -> dict[str, dict]:
    resp = requests.get(f"{LINDY_API_BASE}/agents", headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return {a["name"]: a for a in resp.json().get("agents", [])}


def deploy_agent(config: dict, existing: dict) -> str:
    name = config["name"]
    if name in existing:
        agent_id = existing[name]["id"]
        resp = requests.patch(
            f"{LINDY_API_BASE}/agents/{agent_id}",
            headers=HEADERS, json=config, timeout=15,
        )
        resp.raise_for_status()
        print(f"  [UPDATE] {name} ({agent_id})")
        return agent_id
    else:
        resp = requests.post(
            f"{LINDY_API_BASE}/agents", headers=HEADERS, json=config, timeout=15,
        )
        resp.raise_for_status()
        agent_id = resp.json()["id"]
        print(f"  [CREATE] {name} ({agent_id})")
        return agent_id


def deploy_all(config_dir: str) -> None:
    configs = list(Path(config_dir).glob("*.json"))
    if not configs:
        print(f"No agent configs found in {config_dir}")
        sys.exit(1)
    print(f"Deploying {len(configs)} agents...")
    existing = get_existing_agents()
    deployed = []
    for cfg_file in sorted(configs):
        config = json.loads(cfg_file.read_text())
        agent_id = deploy_agent(config, existing)
        deployed.append({"name": config["name"], "id": agent_id})
    print(f"\nDeployed {len(deployed)} agents.")
    Path("lindy-deployment.json").write_text(json.dumps(deployed, indent=2))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--config-dir", default="lindy-agents/")
    deploy_all(p.parse_args().config_dir)
```

## Advanced Patterns

### Rollback on Failure

```python
import os
import requests

LINDY_API_BASE = "https://api.lindy.ai/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}", "Content-Type": "application/json"}

def deploy_with_rollback(agent_id: str, new_config: dict, backup_config: dict) -> bool:
    try:
        requests.patch(
            f"{LINDY_API_BASE}/agents/{agent_id}",
            headers=HEADERS, json=new_config, timeout=15,
        ).raise_for_status()
        print(f"[OK] Deployed {new_config['name']}")
        return True
    except Exception as e:
        print(f"[ERROR] Deploy failed: {e}. Rolling back...")
        try:
            requests.patch(
                f"{LINDY_API_BASE}/agents/{agent_id}",
                headers=HEADERS, json=backup_config, timeout=15,
            ).raise_for_status()
            print("[OK] Rollback successful")
        except Exception as re:
            print(f"[CRITICAL] Rollback also failed: {re}")
        return False
```

## Troubleshooting

### Deployment Succeeds but Agent Does Not Run

1. Check that `enabled: true` is set in the deployed config
2. Verify trigger conditions are configured correctly
3. Confirm all required integrations are connected
4. Check for duplicate agent names

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
