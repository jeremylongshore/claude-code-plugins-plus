# Team Setup — Runnable Examples

## Python — User-Attributed API Calls

```python
import os
import json
from datetime import datetime
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def team_complete(prompt: str, user_id: str, team: str = "engineering",
                  model: str = "openai/gpt-3.5-turbo") -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        extra_headers={
            "X-Title": f"{team}/{user_id}",
        },
    )
    return {
        "content": response.choices[0].message.content,
        "user_id": user_id,
        "team": team,
        "model": response.model,
        "tokens": response.usage.total_tokens,
    }


def tracked_complete(prompt: str, user_id: str, team: str) -> str:
    result = team_complete(prompt, user_id, team)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "team": team,
        "model": result["model"],
        "tokens": result["tokens"],
    }
    with open("usage-audit.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return result["content"]


print(tracked_complete("Summarize agile methodology", user_id="alice", team="product"))
print(tracked_complete("Write a Python sort function", user_id="bob", team="engineering"))
```

## Python — Per-User Budget Enforcement

```python
import os
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL_COST_PER_M = {
    "openai/gpt-3.5-turbo": 1.0,
    "anthropic/claude-3.5-sonnet": 15.0,
    "google/gemma-2-9b-it:free": 0.0,
}

DAILY_BUDGET_USD = {"free_tier": 0.10, "standard": 1.00, "premium": 10.00}


class UserBudgetTracker:
    def __init__(self, db_path: str = "budgets.json"):
        self.db_path = Path(db_path)
        self._data: dict = json.loads(self.db_path.read_text()) if self.db_path.exists() else {}

    def _user_key(self, user_id: str) -> str:
        from datetime import date
        return f"{user_id}:{date.today().isoformat()}"

    def get_spent(self, user_id: str) -> float:
        return self._data.get(self._user_key(user_id), 0.0)

    def add_spend(self, user_id: str, tokens: int, model: str) -> float:
        cost = tokens * MODEL_COST_PER_M.get(model, 1.0) / 1_000_000
        key = self._user_key(user_id)
        self._data[key] = self._data.get(key, 0.0) + cost
        self.db_path.write_text(json.dumps(self._data, indent=2))
        return cost

    def check_budget(self, user_id: str, tier: str = "standard") -> bool:
        return self.get_spent(user_id) < DAILY_BUDGET_USD.get(tier, 1.00)


tracker = UserBudgetTracker()

def budget_complete(prompt: str, user_id: str, tier: str = "standard") -> str:
    if not tracker.check_budget(user_id, tier):
        raise RuntimeError(f"Daily budget exceeded for {user_id}")

    model = "google/gemma-2-9b-it:free" if tier == "free_tier" else "openai/gpt-3.5-turbo"
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], max_tokens=300,
    )
    cost = tracker.add_spend(user_id, response.usage.total_tokens, model)
    print(f"[Budget] {user_id}: +${cost:.4f} (total ${tracker.get_spent(user_id):.4f} today)")
    return response.choices[0].message.content


print(budget_complete("What is Python?", "alice", "standard"))
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
