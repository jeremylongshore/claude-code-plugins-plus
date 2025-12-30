---
name: openrouter-team-setup
description: |
  Configure OpenRouter for teams. Triggers on "openrouter team",
  "openrouter organization", "openrouter multiple users", "share openrouter".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Team Setup

## API Key Strategy for Teams

### Separate Keys Per Environment
```
Development:
  Key: sk-or-dev-xxx
  Label: "Development"
  Limit: $10.00

Staging:
  Key: sk-or-stg-xxx
  Label: "Staging"
  Limit: $50.00

Production:
  Key: sk-or-prod-xxx
  Label: "Production"
  Limit: $500.00
```

### Keys Per Team/Service
```
Frontend Team:
  Key: sk-or-frontend-xxx
  Label: "Frontend"
  Limit: $100.00

Backend Team:
  Key: sk-or-backend-xxx
  Label: "Backend"
  Limit: $200.00

Data Team:
  Key: sk-or-data-xxx
  Label: "Data Processing"
  Limit: $300.00
```

## Team Configuration

### Shared Configuration
```python
# team_config.py
from dataclasses import dataclass
from typing import Optional, List
import os

@dataclass
class TeamMember:
    name: str
    email: str
    role: str  # "admin", "developer", "viewer"
    api_key_access: List[str]  # Which keys they can use

@dataclass
class TeamConfig:
    name: str
    default_model: str
    allowed_models: List[str]
    budget_limit: float
    members: List[TeamMember]

# Example configuration
TEAM_CONFIG = TeamConfig(
    name="Engineering Team",
    default_model="anthropic/claude-3.5-sonnet",
    allowed_models=[
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-70b-instruct",
    ],
    budget_limit=1000.00,
    members=[
        TeamMember("Alice", "alice@company.com", "admin", ["prod", "dev"]),
        TeamMember("Bob", "bob@company.com", "developer", ["dev"]),
        TeamMember("Carol", "carol@company.com", "developer", ["dev"]),
    ]
)
```

### Role-Based Access
```python
class TeamOpenRouter:
    def __init__(self, team_config: TeamConfig):
        self.config = team_config
        self.keys = {
            "prod": os.environ.get("OPENROUTER_PROD_KEY"),
            "dev": os.environ.get("OPENROUTER_DEV_KEY"),
        }

    def get_client_for_user(self, email: str, environment: str = "dev"):
        # Find user
        member = next(
            (m for m in self.config.members if m.email == email),
            None
        )
        if not member:
            raise PermissionError(f"User {email} not in team")

        # Check access
        if environment not in member.api_key_access:
            raise PermissionError(
                f"User {email} doesn't have access to {environment}"
            )

        # Return client
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.keys[environment],
            default_headers={"X-Title": f"{self.config.name} - {email}"}
        )

    def chat(self, email: str, prompt: str, model: str = None, **kwargs):
        # Validate model
        model = model or self.config.default_model
        if model not in self.config.allowed_models:
            raise ValueError(
                f"Model {model} not allowed. Use: {self.config.allowed_models}"
            )

        client = self.get_client_for_user(email)
        return client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

team_router = TeamOpenRouter(TEAM_CONFIG)
```

## Tracking by User

### User Attribution
```python
class TrackedTeamClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.usage_log = []

    def chat(
        self,
        prompt: str,
        user_id: str,
        model: str = "anthropic/claude-3.5-sonnet",
        **kwargs
    ):
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

        # Log usage
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "model": model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "latency_ms": (time.time() - start_time) * 1000
        })

        return response

    def get_user_usage(self, user_id: str) -> dict:
        user_logs = [l for l in self.usage_log if l["user_id"] == user_id]
        return {
            "user_id": user_id,
            "total_requests": len(user_logs),
            "total_tokens": sum(
                l["prompt_tokens"] + l["completion_tokens"]
                for l in user_logs
            )
        }

    def get_team_summary(self) -> dict:
        by_user = {}
        for log in self.usage_log:
            uid = log["user_id"]
            if uid not in by_user:
                by_user[uid] = {"requests": 0, "tokens": 0}
            by_user[uid]["requests"] += 1
            by_user[uid]["tokens"] += (
                log["prompt_tokens"] + log["completion_tokens"]
            )
        return by_user
```

### HTTP Headers for Tracking
```python
def create_team_client(user_email: str, team_name: str):
    """Create client with tracking headers."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={
            "HTTP-Referer": f"https://{team_name}.company.com",
            "X-Title": f"{team_name} - {user_email}",
        }
    )
```

## Budget Management

### Per-User Budgets
```python
class BudgetManager:
    def __init__(self):
        self.budgets = {}  # user_id -> budget
        self.spent = {}    # user_id -> amount spent

    def set_budget(self, user_id: str, amount: float):
        self.budgets[user_id] = amount
        if user_id not in self.spent:
            self.spent[user_id] = 0.0

    def can_spend(self, user_id: str, amount: float) -> bool:
        budget = self.budgets.get(user_id, float('inf'))
        spent = self.spent.get(user_id, 0.0)
        return spent + amount <= budget

    def record_spend(self, user_id: str, amount: float):
        self.spent[user_id] = self.spent.get(user_id, 0.0) + amount

    def get_remaining(self, user_id: str) -> float:
        budget = self.budgets.get(user_id, float('inf'))
        spent = self.spent.get(user_id, 0.0)
        return budget - spent

budget_mgr = BudgetManager()
budget_mgr.set_budget("user123", 50.00)  # $50/month

def budget_checked_chat(user_id: str, prompt: str, model: str):
    # Estimate cost
    estimated_cost = 0.01  # Rough estimate

    if not budget_mgr.can_spend(user_id, estimated_cost):
        raise Exception("Budget exceeded")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Calculate actual cost
    actual_cost = calculate_cost(response, model)
    budget_mgr.record_spend(user_id, actual_cost)

    return response
```

### Team Budget Dashboard
```python
class TeamBudgetDashboard:
    def __init__(self, team_budget: float):
        self.team_budget = team_budget
        self.user_spending = {}

    def record_usage(
        self,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        if user_id not in self.user_spending:
            self.user_spending[user_id] = []

        self.user_spending[user_id].append({
            "timestamp": datetime.now(),
            "model": model,
            "tokens": prompt_tokens + completion_tokens,
            "cost": cost
        })

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        prices = {
            "anthropic/claude-3.5-sonnet": (0.003, 0.015),
            "anthropic/claude-3-haiku": (0.00025, 0.00125),
            "openai/gpt-4-turbo": (0.01, 0.03),
        }
        prompt_price, completion_price = prices.get(model, (0.01, 0.03))
        return (
            prompt_tokens * prompt_price / 1000 +
            completion_tokens * completion_price / 1000
        )

    def get_dashboard(self) -> dict:
        total_spent = sum(
            sum(u["cost"] for u in usage)
            for usage in self.user_spending.values()
        )

        return {
            "team_budget": self.team_budget,
            "total_spent": total_spent,
            "remaining": self.team_budget - total_spent,
            "utilization": total_spent / self.team_budget * 100,
            "by_user": {
                user: sum(u["cost"] for u in usage)
                for user, usage in self.user_spending.items()
            }
        }
```

## Access Control

### Model Access by Role
```python
ROLE_MODEL_ACCESS = {
    "admin": [
        "anthropic/claude-3-opus",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "openai/gpt-4",
        "openai/gpt-3.5-turbo",
    ],
    "developer": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
    ],
    "intern": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct",
    ]
}

def get_allowed_models(role: str) -> list:
    return ROLE_MODEL_ACCESS.get(role, ROLE_MODEL_ACCESS["intern"])

def role_checked_chat(user_role: str, model: str, prompt: str):
    allowed = get_allowed_models(user_role)

    if model not in allowed:
        raise PermissionError(
            f"Model {model} not available for role {user_role}. "
            f"Allowed: {allowed}"
        )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## Shared Services Setup

### Central LLM Service
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# User database (in practice, use real auth)
USERS = {
    "token123": {"user_id": "alice", "role": "admin"},
    "token456": {"user_id": "bob", "role": "developer"},
}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    if token not in USERS:
        raise HTTPException(status_code=401, detail="Invalid token")
    return USERS[token]

@app.post("/chat")
async def chat(
    prompt: str,
    model: str = "anthropic/claude-3.5-sonnet",
    user: dict = Depends(get_current_user)
):
    # Check model access
    allowed = get_allowed_models(user["role"])
    if model not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Model {model} not allowed for your role"
        )

    # Check budget
    if not budget_mgr.can_spend(user["user_id"], 0.01):
        raise HTTPException(status_code=402, detail="Budget exceeded")

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Track usage
    tracker.record(user["user_id"], model, response)

    return {"response": response.choices[0].message.content}
```
