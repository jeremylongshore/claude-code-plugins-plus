# Api Key Wrapper With Team Context

## API Key Wrapper with Team Context

```python
import requests
from functools import wraps

class TeamKlingAIClient:
    """Kling AI client with team context and permissions."""

    def __init__(self, team_manager: TeamManager, user_email: str):
        self.team_manager = team_manager
        self.user_email = user_email
        self.base_url = "https://api.klingai.com/v1"

    def generate_video(self, project_id: str, prompt: str, **params) -> dict:
        """Generate video with team context."""
        # Check permission
        if not self.team_manager.check_permission(
            self.user_email, project_id, "generate"
        ):
            raise PermissionError(
                f"User {self.user_email} cannot generate videos in {project_id}"
            )

        # Get project API key
        project = next(
            (p for p in self.team_manager.config.projects if p.id == project_id),
            None
        )
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Make request with project key
        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {project.api_key}",
                "Content-Type": "application/json",
                "X-Project-ID": project_id,
                "X-User-Email": self.user_email
            },
            json={
                "prompt": prompt,
                **params
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
manager = TeamManager()
manager.load_config()

client = TeamKlingAIClient(manager, "bob@acme.com")

# Bob can generate in marketing project
result = client.generate_video(
    project_id="proj_marketing",
    prompt="Summer sale promotional video",
    duration=5
)
```
