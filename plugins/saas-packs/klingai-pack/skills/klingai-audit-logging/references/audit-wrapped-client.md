# Audit-Wrapped Client

## Audit-Wrapped Client

```python
class AuditedKlingAIClient:
    """Kling AI client with comprehensive audit logging."""

    def __init__(
        self,
        api_key: str,
        audit_logger: AuditLogger,
        user_id: str
    ):
        self.api_key = api_key
        self.audit = audit_logger
        self.user_id = user_id
        self.base_url = "https://api.klingai.com/v1"

    def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5",
        ip_address: str = None
    ) -> Dict:
        """Generate video with full audit trail."""
        import requests

        # Log prompt submission
        self.audit.log(
            event_type=AuditEventType.PROMPT_SUBMITTED,
            actor_id=self.user_id,
            resource_type="prompt",
            action="submit_prompt",
            ip_address=ip_address,
            prompt_length=len(prompt),
            model=model,
            duration=duration
        )

        # Log generation start
        self.audit.log(
            event_type=AuditEventType.GENERATION_STARTED,
            actor_id=self.user_id,
            resource_type="video",
            action="start_generation",
            model=model,
            duration=duration
        )

        try:
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

            if response.status_code == 200:
                result = response.json()
                job_id = result["job_id"]

                # Log success
                self.audit.log(
                    event_type=AuditEventType.GENERATION_STARTED,
                    actor_id=self.user_id,
                    resource_type="video",
                    resource_id=job_id,
                    action="generation_submitted",
                    outcome="success"
                )

                return result

            elif response.status_code == 429:
                # Log rate limit
                self.audit.log(
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    actor_id=self.user_id,
                    resource_type="api",
                    action="rate_limit_hit",
                    outcome="blocked"
                )
                raise Exception("Rate limit exceeded")

            else:
                # Log failure
                self.audit.log(
                    event_type=AuditEventType.GENERATION_FAILED,
                    actor_id=self.user_id,
                    resource_type="video",
                    action="generation_failed",
                    outcome="failure",
                    error_code=response.status_code
                )
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            self.audit.log(
                event_type=AuditEventType.GENERATION_FAILED,
                actor_id=self.user_id,
                resource_type="video",
                action="generation_error",
                outcome="failure",
                error=str(e)
            )
            raise

# Usage
audit_logger = AuditLogger(include_pii=False)

client = AuditedKlingAIClient(
    api_key=os.environ["KLINGAI_API_KEY"],
    audit_logger=audit_logger,
    user_id="user@example.com"
)

# Generate with auditing
try:
    result = client.generate_video(
        prompt="A serene mountain lake at sunrise",
        duration=5,
        ip_address="192.168.1.100"
    )
except Exception as e:
    print(f"Error: {e}")

# Check user activity
activity = audit_logger.get_user_activity("us***@example.com")
print(json.dumps(activity, indent=2))

# Verify integrity
integrity = audit_logger.verify_integrity()
print(f"Log integrity: {integrity['integrity_ok']}")
```
