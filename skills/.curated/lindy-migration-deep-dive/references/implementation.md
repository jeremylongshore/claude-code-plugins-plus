# Lindy Migration Deep Dive -- Implementation Details

## Pre-Migration Audit

Document all current automations before migration:

```python
import json
import os
from pathlib import Path

def audit_existing_automations(export_dir: str = "export/zaps/") -> dict:
    """Document all current automations before migration."""
    audit = {
        "source_platform": "zapier",
        "total_automations": 0,
        "active_automations": [],
        "monthly_run_estimate": 0,
    }

    config_dir = Path(export_dir)
    if config_dir.exists():
        for cfg_file in config_dir.glob("*.json"):
            config = json.loads(cfg_file.read_text())
            if config.get("status") == "on":
                audit["active_automations"].append({
                    "name": config["title"],
                    "trigger": config.get("trigger", {}).get("app"),
                    "actions": [a.get("app") for a in config.get("actions", [])],
                    "runs_30d": config.get("stats", {}).get("runs_30d", 0),
                })
                audit["total_automations"] += 1

    # Sort by usage -- migrate highest-traffic automations first
    audit["active_automations"].sort(key=lambda x: x["runs_30d"], reverse=True)
    return audit


def save_migration_plan(audit: dict) -> None:
    Path("migration-plan.json").write_text(json.dumps(audit, indent=2))
    print(f"Migration plan: {audit['total_automations']} automations")
    high_priority = [a for a in audit['active_automations'] if a['runs_30d'] > 100]
    print(f"High priority (100+ runs/month): {len(high_priority)}")
```

## Parallel Running During Migration

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_run_comparison(old_fn, lindy_fn, test_inputs: list[dict]) -> dict:
    """Run both old automation and Lindy agent with same inputs to verify parity."""
    results = {"matches": 0, "mismatches": 0, "errors": 0}
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=4) as executor:
        for inputs in test_inputs:
            old_result = error_old = None
            lindy_result = error_lindy = None

            try:
                old_result = await loop.run_in_executor(executor, old_fn, inputs)
            except Exception as e:
                error_old = str(e)

            try:
                lindy_result = await loop.run_in_executor(executor, lindy_fn, inputs)
            except Exception as e:
                error_lindy = str(e)

            if error_old or error_lindy:
                results["errors"] += 1
            elif old_result == lindy_result:
                results["matches"] += 1
            else:
                results["mismatches"] += 1

    total = len(test_inputs)
    results["parity_rate"] = f"{results['matches'] / total:.0%}" if total else "N/A"
    return results
```

## Advanced Patterns

### Incremental Traffic Migration

```python
import random

class TrafficMigrator:
    def __init__(self, lindy_percentage: float = 0.0):
        """lindy_percentage: 0.0 = all old, 1.0 = all Lindy"""
        self.lindy_percentage = lindy_percentage
        self.old_count = 0
        self.lindy_count = 0

    def route(self, inputs: dict) -> str:
        if random.random() < self.lindy_percentage:
            self.lindy_count += 1
            return "lindy"
        self.old_count += 1
        return "old"

    def increase_lindy_traffic(self, by: float = 0.1) -> float:
        self.lindy_percentage = min(1.0, self.lindy_percentage + by)
        return self.lindy_percentage

    def stats(self) -> dict:
        total = self.old_count + self.lindy_count
        return {
            "lindy_pct_config": f"{self.lindy_percentage:.0%}",
            "lindy_actual": f"{self.lindy_count / max(1, total):.0%}",
        }


# Usage: start at 10%, increase as confidence grows
migrator = TrafficMigrator(lindy_percentage=0.1)
```

## Troubleshooting

### Agent Produces Different Results Than Old Automation

1. Check if old automation had hidden state (stored context or session variables)
2. Verify all integrations are reconnected in Lindy
3. Compare trigger event formats -- small differences can cause different behavior
4. Review AI step prompts -- rephrase to match expected output format

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
