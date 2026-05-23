# Policy Violation Logger

## Policy Violation Logger

```python
from datetime import datetime
import json

class PolicyViolationLogger:
    """Log and track content policy violations."""

    def __init__(self, log_path: str = "policy_violations.json"):
        self.log_path = log_path
        self.violations = []
        self.load()

    def load(self):
        """Load existing violations."""
        try:
            with open(self.log_path) as f:
                self.violations = json.load(f)
        except FileNotFoundError:
            self.violations = []

    def save(self):
        """Save violations to file."""
        with open(self.log_path, "w") as f:
            json.dump(self.violations, f, indent=2)

    def log_violation(
        self,
        prompt: str,
        user_id: str,
        flags: List[str],
        action: str = "blocked"
    ):
        """Log a policy violation."""
        violation = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "prompt_hash": hash(prompt),  # Don't store actual violating content
            "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "flags": flags,
            "action": action
        }

        self.violations.append(violation)
        self.save()

        # Check for repeat offenders
        user_violations = [v for v in self.violations if v["user_id"] == user_id]
        if len(user_violations) >= 3:
            print(f"WARNING: User {user_id} has {len(user_violations)} violations")

    def get_violation_stats(self) -> Dict:
        """Get violation statistics."""
        if not self.violations:
            return {"total": 0}

        flag_counts = {}
        for v in self.violations:
            for flag in v["flags"]:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

        return {
            "total": len(self.violations),
            "by_flag": flag_counts,
            "unique_users": len(set(v["user_id"] for v in self.violations))
        }
```
