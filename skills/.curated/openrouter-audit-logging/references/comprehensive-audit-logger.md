# Comprehensive Audit Logger

## Comprehensive Audit Logger

### Base Logger Implementation

```python
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import uuid

@dataclass
class AuditEntry:
    """Single audit log entry."""
    id: str
    timestamp: str
    event_type: str
    user_id: str
    model: str
    prompt_hash: str
    response_hash: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    status: str  # success, error
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogger:
    """Production audit logging for OpenRouter."""

    def __init__(self, output_path: str = "audit_logs"):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)

    def _hash(self, content: str) -> str:
        """Create SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_log_file(self) -> str:
        """Get current log file path (daily rotation)."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return os.path.join(self.output_path, f"audit_{date_str}.jsonl")

    def log(self, entry: AuditEntry):
        """Write audit entry to log file."""
        log_file = self._get_log_file()
        with open(log_file, 'a') as f:
            f.write(json.dumps(asdict(entry)) + '\n')

    def create_entry(
        self,
        user_id: str,
        model: str,
        prompt: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        status: str = "success",
        error_type: str = None,
        metadata: dict = None
    ) -> AuditEntry:
        """Create audit entry from request/response."""
        return AuditEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type="chat_completion",
            user_id=user_id,
            model=model,
            prompt_hash=self._hash(prompt),
            response_hash=self._hash(response),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            status=status,
            error_type=error_type,
            metadata=metadata
        )

audit_logger = AuditLogger()
```

### Instrumented Client

```python
import time

class AuditedOpenRouterClient:
    """OpenRouter client with built-in audit logging."""

    def __init__(self, api_key: str, audit_logger: AuditLogger):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.audit = audit_logger

    def chat(
        self,
        prompt: str,
        user_id: str,
        model: str = "openai/gpt-4-turbo",
        metadata: dict = None,
        **kwargs
    ) -> str:
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            latency = (time.time() - start_time) * 1000
            content = response.choices[0].message.content

            # Log success
            entry = self.audit.create_entry(
                user_id=user_id,
                model=model,
                prompt=prompt,
                response=content,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                latency_ms=latency,
                status="success",
                metadata=metadata
            )
            self.audit.log(entry)

            return content

        except Exception as e:
            latency = (time.time() - start_time) * 1000

            # Log error
            entry = self.audit.create_entry(
                user_id=user_id,
                model=model,
                prompt=prompt,
                response="",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency,
                status="error",
                error_type=type(e).__name__,
                metadata=metadata
            )
            self.audit.log(entry)

            raise

audited_client = AuditedOpenRouterClient(
    api_key=os.environ["OPENROUTER_API_KEY"],
    audit_logger=audit_logger
)
```
