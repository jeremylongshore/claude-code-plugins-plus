---
name: vastai-enterprise-rbac
description: |
  Implement team access control and spending governance for Vast.ai GPU cloud.
  Use when managing multi-team GPU access, implementing spending controls,
  or setting up API key separation for different teams.
  Trigger with phrases like "vastai team access", "vastai RBAC",
  "vastai enterprise", "vastai spending controls", "vastai permissions".
allowed-tools: Read, Write, Edit, Bash(vastai:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, rbac]

---
# Vast.ai Enterprise RBAC

## Overview
Control access to Vast.ai GPU instances and spending through API key management, team-level budgets, and GPU allocation policies. Vast.ai uses a marketplace model with per-GPU-hour pricing (RTX 4090 ~$0.20/hr, A100 ~$1.50/hr, H100 ~$3.00/hr).

## Prerequisites
- Vast.ai account(s) with API keys
- Understanding of team GPU usage patterns
- Budget allocation per team/project

## Instructions

### Step 1: Team API Key Strategy

```python
# Separate API keys per team for billing isolation
# Option A: Separate Vast.ai accounts per team
# Option B: Single account with application-level controls

TEAM_CONFIGS = {
    "ml-research": {
        "api_key_env": "VASTAI_KEY_RESEARCH",
        "gpu_whitelist": ["A100", "H100_SXM"],
        "max_instances": 8,
        "daily_budget": 200.00,
        "max_dph": 4.00,
    },
    "ml-engineering": {
        "api_key_env": "VASTAI_KEY_ENGINEERING",
        "gpu_whitelist": ["RTX_4090", "A100"],
        "max_instances": 4,
        "daily_budget": 50.00,
        "max_dph": 2.00,
    },
    "data-science": {
        "api_key_env": "VASTAI_KEY_DATASCIENCE",
        "gpu_whitelist": ["RTX_4090", "RTX_3090"],
        "max_instances": 2,
        "daily_budget": 10.00,
        "max_dph": 0.30,
    },
}
```

### Step 2: Policy Enforcement Layer

```python
class VastPolicyEnforcer:
    def __init__(self, team_config):
        self.config = team_config
        self.client = VastClient(api_key=os.environ[team_config["api_key_env"]])

    def can_provision(self, gpu_name, num_gpus=1):
        """Check if provisioning is allowed by team policy."""
        if gpu_name not in self.config["gpu_whitelist"]:
            return False, f"GPU {gpu_name} not in team whitelist"

        running = len([i for i in self.client.show_instances()
                      if i.get("actual_status") == "running"])
        if running >= self.config["max_instances"]:
            return False, f"Instance limit reached ({running}/{self.config['max_instances']})"

        return True, "OK"

    def provision_with_policy(self, gpu_name, image, disk_gb=20):
        allowed, reason = self.can_provision(gpu_name)
        if not allowed:
            raise PermissionError(f"Policy violation: {reason}")

        offers = self.client.search_offers({
            "gpu_name": {"eq": gpu_name},
            "dph_total": {"lte": self.config["max_dph"]},
            "reliability2": {"gte": 0.95},
            "rentable": {"eq": True},
        })
        if not offers.get("offers"):
            raise RuntimeError("No offers matching policy constraints")

        return self.client.create_instance(
            offers["offers"][0]["id"], image, disk_gb)
```

### Step 3: Audit Logging

```python
import json, datetime

class AuditLogger:
    def __init__(self, log_file="vast_audit.jsonl"):
        self.log_file = log_file

    def log(self, team, action, details):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "team": team,
            "action": action,
            **details,
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

# Usage
audit = AuditLogger()
audit.log("ml-research", "provision", {
    "gpu": "A100", "offer_id": 12345, "dph": 1.50})
audit.log("ml-research", "destroy", {
    "instance_id": 67890, "duration_hours": 4.2, "total_cost": 6.30})
```

### Step 4: Spending Reports

```python
def team_spending_report(audit_file="vast_audit.jsonl"):
    """Generate spending report from audit log."""
    import json
    costs = {}
    with open(audit_file) as f:
        for line in f:
            entry = json.loads(line)
            if entry["action"] == "destroy" and "total_cost" in entry:
                team = entry["team"]
                costs.setdefault(team, 0)
                costs[team] += entry["total_cost"]

    print("Team Spending Report:")
    for team, cost in sorted(costs.items(), key=lambda x: -x[1]):
        print(f"  {team}: ${cost:.2f}")
```

## Output
- Team-specific API key configuration
- Policy enforcement layer (GPU whitelist, instance limits, budget caps)
- Audit logging for all provisioning and destruction events
- Spending reports per team

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Policy violation on provision | GPU not in whitelist or limit reached | Request policy change or destroy idle instances |
| Budget exceeded | Team exceeded daily limit | Alert team lead; pause provisioning until next day |
| Missing API key | Environment variable not set | Configure key in secrets manager |
| Audit log missing entries | Logger not wired into all operations | Audit the code paths for missing log calls |

## Resources
- [Vast.ai Account](https://cloud.vast.ai)
- [REST API](https://vast.ai/developers/api)

## Next Steps
For migration strategies, see `vastai-migration-deep-dive`.

## Examples

**Team onboarding**: Create a new team config entry with conservative limits (2 instances, RTX 4090 only, $10/day). Increase limits after the team demonstrates responsible usage.

**Monthly chargeback**: Parse the audit log to generate per-team invoices for internal cost allocation.
