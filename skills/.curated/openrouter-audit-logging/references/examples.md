# Audit Logging Examples

## Python — Structured Audit Logger

```python
import os
import json
import hashlib
import re
from datetime import datetime, timezone
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

class AuditLogger:
    """Structured audit logger for OpenRouter API calls."""

    PII_PATTERNS = [
        (r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b', '[EMAIL]'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
    ]

    def __init__(self, log_file: str = "audit.jsonl"):
        self.log_file = log_file

    def redact_pii(self, text: str) -> str:
        for pattern, replacement in self.PII_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def log_request(self, user_id: str, model: str, messages: list,
                    response, elapsed_ms: float):
        prompt_text = " ".join(m.get("content", "") for m in messages)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "model": model,
            "prompt_hash": self.hash_content(prompt_text),
            "prompt_preview": self.redact_pii(prompt_text[:100]),
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "status": "success",
            "latency_ms": round(elapsed_ms),
            "generation_id": response.id,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

audit = AuditLogger()

def audited_completion(user_id: str, prompt: str,
                       model: str = "openai/gpt-3.5-turbo") -> str:
    import time
    messages = [{"role": "user", "content": prompt}]

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model, messages=messages, max_tokens=300,
    )
    elapsed = (time.perf_counter() - start) * 1000

    entry = audit.log_request(user_id, model, messages, response, elapsed)
    print(f"[Audit] user={entry['user_id']} tokens={entry['total_tokens']} "
          f"latency={entry['latency_ms']}ms")

    return response.choices[0].message.content

# Usage
result = audited_completion("user-123", "What is machine learning?")
print(result)

# Audit log entry (in audit.jsonl):
# {"timestamp":"2026-03-17T10:00:00Z","user_id":"user-123",
#  "model":"openai/gpt-3.5-turbo","prompt_hash":"a1b2c3d4e5f6g7h8",
#  "prompt_preview":"What is machine learning?","prompt_tokens":12,
#  "completion_tokens":85,"total_tokens":97,"status":"success",
#  "latency_ms":450,"generation_id":"gen-abc123"}
```

## Querying Audit Logs

```python
import json

def query_audit_log(log_file: str = "audit.jsonl", user_id: str = None,
                    model: str = None) -> list[dict]:
    """Query audit logs with optional filters."""
    results = []
    with open(log_file) as f:
        for line in f:
            entry = json.loads(line)
            if user_id and entry["user_id"] != user_id:
                continue
            if model and entry["model"] != model:
                continue
            results.append(entry)
    return results

# Get all requests by a user
user_logs = query_audit_log(user_id="user-123")
total_tokens = sum(e["total_tokens"] for e in user_logs)
print(f"User user-123: {len(user_logs)} requests, {total_tokens} total tokens")
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
