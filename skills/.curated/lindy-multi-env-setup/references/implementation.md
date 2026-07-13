# Lindy Multi-Environment Setup -- Implementation Details

## Environment Configuration

```bash
# .env.development
LINDY_API_KEY=sk-lindy-dev-xxxxx
LINDY_WEBHOOK_SECRET=dev-secret-123
LINDY_ENVIRONMENT=development
LINDY_AGENT_TRIGGER_ENABLED=false

# .env.staging
LINDY_API_KEY=sk-lindy-staging-xxxxx
LINDY_ENVIRONMENT=staging
LINDY_AGENT_TRIGGER_ENABLED=true

# Production: stored in secrets manager, NOT in files
```

### Config Loader

```python
import os
from dataclasses import dataclass
from typing import Literal

Environment = Literal["development", "staging", "production"]

@dataclass
class LindyConfig:
    api_key: str
    webhook_secret: str
    environment: Environment
    agent_trigger_enabled: bool

    def is_production(self) -> bool:
        return self.environment == "production"


def load_lindy_config() -> LindyConfig:
    env = os.environ.get("LINDY_ENVIRONMENT", "development")
    api_key = os.environ.get("LINDY_API_KEY", "")
    if not api_key:
        raise RuntimeError(f"LINDY_API_KEY not set for env '{env}'.")
    return LindyConfig(
        api_key=api_key,
        webhook_secret=os.environ.get("LINDY_WEBHOOK_SECRET", ""),
        environment=env,
        agent_trigger_enabled=os.environ.get("LINDY_AGENT_TRIGGER_ENABLED", "true").lower() == "true",
    )


config = load_lindy_config()
print(f"Lindy: {config.environment} (triggers: {'on' if config.agent_trigger_enabled else 'off'})")
```

## Advanced Patterns

### Per-Environment Agent Naming

```python
def agent_name(base_name: str, env: str) -> str:
    """Production uses the bare name; others include an env suffix."""
    if env == "production":
        return base_name
    return f"{base_name}-{env}"

# production: "customer-support-classifier"
# staging:    "customer-support-classifier-staging"
```

### Multi-Environment Deploy Script

```python
import os
import json
import requests
from pathlib import Path

LINDY_API_BASE = "https://api.lindy.ai/v1"

def get_headers(env: str) -> dict:
    key_var = f"LINDY_API_KEY_{env.upper()}"
    key = os.environ.get(key_var) or os.environ.get("LINDY_API_KEY", "")
    if not key:
        raise RuntimeError(f"No API key for env '{env}'")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def deploy_agent_to_env(config_file: Path, env: str) -> None:
    base_config = json.loads(config_file.read_text())

    # Apply env-specific overrides if they exist
    override_file = config_file.parent / f"{config_file.stem}.{env}.json"
    if override_file.exists():
        base_config.update(json.loads(override_file.read_text()))

    base_config["name"] = agent_name(base_config["name"], env)

    list_resp = requests.get(f"{LINDY_API_BASE}/agents", headers=get_headers(env), timeout=10)
    list_resp.raise_for_status()
    existing = {a["name"]: a["id"] for a in list_resp.json().get("agents", [])}

    name = base_config["name"]
    if name in existing:
        requests.patch(
            f"{LINDY_API_BASE}/agents/{existing[name]}",
            headers=get_headers(env), json=base_config, timeout=15,
        ).raise_for_status()
        print(f"  [{env.upper()}] Updated '{name}'")
    else:
        requests.post(
            f"{LINDY_API_BASE}/agents", headers=get_headers(env), json=base_config, timeout=15,
        ).raise_for_status()
        print(f"  [{env.upper()}] Created '{name}'")


for env in ["development", "staging", "production"]:
    for cfg in Path("lindy-agents/").glob("*.base.json"):
        deploy_agent_to_env(cfg, env)
```

## Troubleshooting

### Agent Works in Staging but Fails in Production

1. Compare environment variables -- check for missing `LINDY_*` vars in production
2. Verify production integrations are connected with production credentials
3. Check for agent name collisions between environments
4. Review webhook endpoints -- do not use staging URLs in production

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
