# Compliance Considerations

## Compliance Considerations

### GDPR Compliance

```python
class GDPRCompliance:
    """GDPR compliance helpers."""

    def __init__(self):
        self.consent_log = {}  # user_id -> consent_timestamp

    def record_consent(self, user_id: str):
        """Record user consent for AI processing."""
        self.consent_log[user_id] = datetime.utcnow().isoformat()

    def has_consent(self, user_id: str) -> bool:
        """Check if user has given consent."""
        return user_id in self.consent_log

    def process_with_consent(
        self,
        user_id: str,
        prompt: str,
        model: str
    ):
        if not self.has_consent(user_id):
            raise PermissionError(
                "User has not consented to AI processing"
            )

        return privacy_safe_chat(prompt, model)

    def right_to_erasure(self, user_id: str, data_stores: list):
        """Handle right to be forgotten requests."""
        for store in data_stores:
            store.delete_user_data(user_id)
        del self.consent_log[user_id]
        return {"status": "erased", "user_id": user_id}

gdpr = GDPRCompliance()
```

### Data Processing Agreement

```
When using OpenRouter for business:

1. Review OpenRouter's DPA (if available)
2. Review each model provider's DPA
3. Document data flows
4. Implement appropriate safeguards
5. Update privacy policies
```
