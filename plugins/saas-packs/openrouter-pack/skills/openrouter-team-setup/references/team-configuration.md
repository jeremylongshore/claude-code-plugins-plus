# Team Configuration

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
