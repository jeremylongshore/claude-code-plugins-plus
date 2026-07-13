# Structured Logging

## Structured Logging

### JSON Lines Format

```python
# audit_2024-01-15.jsonl example:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "event_type": "chat_completion",
  "user_id": "user_123",
  "model": "anthropic/claude-3.5-sonnet",
  "prompt_hash": "a1b2c3d4...",
  "response_hash": "e5f6g7h8...",
  "prompt_tokens": 150,
  "completion_tokens": 450,
  "latency_ms": 1234.5,
  "status": "success",
  "metadata": {
    "session_id": "sess_abc",
    "feature": "code_review"
  }
}
```

### Cloud Logging Integration

```python
# Google Cloud Logging
from google.cloud import logging as cloud_logging

class CloudAuditLogger:
    def __init__(self, project_id: str, log_name: str = "openrouter-audit"):
        self.client = cloud_logging.Client(project=project_id)
        self.logger = self.client.logger(log_name)

    def log(self, entry: AuditEntry):
        self.logger.log_struct(
            asdict(entry),
            severity="INFO" if entry.status == "success" else "ERROR"
        )

# AWS CloudWatch
import boto3

class CloudWatchAuditLogger:
    def __init__(self, log_group: str, log_stream: str):
        self.client = boto3.client('logs')
        self.log_group = log_group
        self.log_stream = log_stream

    def log(self, entry: AuditEntry):
        self.client.put_log_events(
            logGroupName=self.log_group,
            logStreamName=self.log_stream,
            logEvents=[{
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'message': json.dumps(asdict(entry))
            }]
        )
```
