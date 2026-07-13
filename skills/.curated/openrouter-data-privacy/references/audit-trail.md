# Audit Trail

## Audit Trail

### Request Logging

```python
import hashlib
from datetime import datetime
import json

class AuditLogger:
    """Log requests for compliance without storing content."""

    def __init__(self, log_file: str = "audit_log.jsonl"):
        self.log_file = log_file

    def log_request(
        self,
        user_id: str,
        model: str,
        prompt_hash: str,
        metadata: dict = None
    ):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "model": model,
            "prompt_hash": prompt_hash,  # Hash only, not content
            "metadata": metadata or {}
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    @staticmethod
    def hash_content(content: str) -> str:
        """Create hash of content for audit without storing content."""
        return hashlib.sha256(content.encode()).hexdigest()

audit = AuditLogger()

def audited_chat(prompt: str, model: str, user_id: str):
    # Log without storing content
    prompt_hash = audit.hash_content(prompt)
    audit.log_request(user_id, model, prompt_hash)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response
```
