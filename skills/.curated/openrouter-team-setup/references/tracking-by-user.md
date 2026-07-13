# Tracking By User

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
