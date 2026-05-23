# Budget Enforcing Wrapper

## Budget Enforcing Wrapper

```python
class BudgetEnforcedClient:
    """Kling AI client with budget enforcement."""

    def __init__(self, api_key: str, tracker: CostTracker, project_id: str):
        self.api_key = api_key
        self.tracker = tracker
        self.project_id = project_id
        self.base_url = "https://api.klingai.com/v1"

    def generate_video(self, prompt: str, duration: int = 5, model: str = "kling-v1.5") -> dict:
        """Generate video with budget check."""
        # Pre-flight budget check
        check = self.tracker.can_generate(self.project_id, duration, model)

        if not check["allowed"]:
            raise BudgetExceededError(
                f"Budget exceeded for {self.project_id}. "
                f"Need {check['credits_needed']} credits, "
                f"have {check['credits_remaining']}"
            )

        # Make API request
        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "duration": duration,
                "model": model
            }
        )
        response.raise_for_status()
        result = response.json()

        # Record usage
        self.tracker.record_usage(
            job_id=result["job_id"],
            duration=duration,
            model=model,
            project_id=self.project_id
        )

        return result

class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""
    pass
```
