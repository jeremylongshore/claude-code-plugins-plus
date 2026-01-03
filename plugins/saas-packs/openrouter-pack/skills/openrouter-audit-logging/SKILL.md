---
name: openrouter-audit-logging
description: |
  Implement audit logging for OpenRouter compliance. Use when meeting regulatory requirements or security audits. Trigger with phrases like 'openrouter audit', 'openrouter compliance log', 'openrouter security log', 'audit trail'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Audit Logging

## Overview

This skill demonstrates implementing comprehensive audit logging for security, compliance, and operational visibility.

## Prerequisites

- OpenRouter integration
- Audit requirements defined
- Log storage infrastructure

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates implementing comprehensive audit logging for security, compliance, and operational visibility.

## Prerequisites

- OpenRouter integration
- Audit requirements defined
- Log storage infrastructure

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

## Log Analysis

### Query Audit Logs
```python
def query_logs(
    log_dir: str,
    user_id: str = None,
    model: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None
) -> list[AuditEntry]:
    """Query audit logs with filters."""
    results = []

    # Get log files in date range
    log_files = sorted(Path(log_dir).glob("audit_*.jsonl"))

    for log_file in log_files:
        file_date = log_file.stem.split("_")[1]

        if start_date and file_date < start_date:
            continue
        if end_date and file_date > end_date:
            continue

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # Apply filters
                if user_id and entry.get("user_id") != user_id:
                    continue
                if model and entry.get("model") != model:
                    continue
                if status and entry.get("status") != status:
                    continue

                results.append(entry)

    return results

# Example queries
user_logs = query_logs("audit_logs", user_id="user_123")
error_logs = query_logs("audit_logs", status="error")
```

### Generate Audit Report
```python
def generate_audit_report(log_dir: str, days: int = 7) -> dict:
    """Generate audit report for compliance."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    logs = query_logs(
        log_dir,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    # Aggregate statistics
    total_requests = len(logs)
    successful = sum(1 for l in logs if l["status"] == "success")
    failed = sum(1 for l in logs if l["status"] == "error")

    by_user = {}
    by_model = {}
    total_tokens = 0
    total_latency = 0

    for log in logs:
        user = log["user_id"]
        model = log["model"]

        by_user[user] = by_user.get(user, 0) + 1
        by_model[model] = by_model.get(model, 0) + 1
        total_tokens += log["prompt_tokens"] + log["completion_tokens"]
        total_latency += log["latency_ms"]

    return {
        "report_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "summary": {
            "total_requests": total_requests,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_requests if total_requests else 0,
            "total_tokens": total_tokens,
            "avg_latency_ms": total_latency / total_requests if total_requests else 0
        },
        "by_user": dict(sorted(by_user.items(), key=lambda x: -x[1])),
        "by_model": dict(sorted(by_model.items(), key=lambda x: -x[1])),
        "error_breakdown": {
            log["error_type"]: 1
            for log in logs if log["status"] == "error"
        }
    }
```

## Log Retention & Archival

### Retention Policy
```python
class LogRetentionManager:
    """Manage log retention and archival."""

    def __init__(
        self,
        log_dir: str,
        retention_days: int = 90,
        archive_after_days: int = 30
    ):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.archive_after_days = archive_after_days

    def get_log_date(self, filename: str) -> date:
        """Extract date from log filename."""
        date_str = filename.replace("audit_", "").replace(".jsonl", "")
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def run_retention(self):
        """Apply retention policy."""
        today = date.today()
        archived = []
        deleted = []

        for log_file in self.log_dir.glob("audit_*.jsonl"):
            log_date = self.get_log_date(log_file.stem)
            age_days = (today - log_date).days

            if age_days > self.retention_days:
                # Delete old logs
                log_file.unlink()
                deleted.append(log_file.name)

            elif age_days > self.archive_after_days:
                # Archive to compressed format
                self._archive_log(log_file)
                archived.append(log_file.name)

        return {"archived": archived, "deleted": deleted}

    def _archive_log(self, log_file: Path):
        """Compress and archive log file."""
        import gzip
        import shutil

        archive_dir = self.log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        archive_path = archive_dir / (log_file.name + ".gz")
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        log_file.unlink()

retention_manager = LogRetentionManager(
    "audit_logs",
    retention_days=90,
    archive_after_days=30
)
```

## Compliance Features

### Tamper Detection
```python
import hmac

class TamperProofLogger:
    """Audit logger with tamper detection."""

    def __init__(self, secret_key: str, base_logger: AuditLogger):
        self.secret_key = secret_key.encode()
        self.base_logger = base_logger
        self.previous_hash = None

    def _sign_entry(self, entry: dict) -> str:
        """Create HMAC signature of entry."""
        content = json.dumps(entry, sort_keys=True)
        signature = hmac.new(
            self.secret_key,
            content.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def log(self, entry: AuditEntry):
        entry_dict = asdict(entry)

        # Add chain hash for tamper detection
        chain_content = json.dumps(entry_dict, sort_keys=True)
        if self.previous_hash:
            chain_content = self.previous_hash + chain_content

        entry_dict["chain_hash"] = hashlib.sha256(
            chain_content.encode()
        ).hexdigest()
        entry_dict["signature"] = self._sign_entry(entry_dict)

        self.previous_hash = entry_dict["chain_hash"]

        # Write to base logger
        with open(self.base_logger._get_log_file(), 'a') as f:
            f.write(json.dumps(entry_dict) + '\n')

    def verify_chain(self, log_file: str) -> bool:
        """Verify log chain integrity."""
        previous_hash = None

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # Verify signature
                stored_sig = entry.pop("signature")
                expected_sig = self._sign_entry(entry)
                if stored_sig != expected_sig:
                    return False

                # Verify chain
                stored_chain = entry["chain_hash"]
                entry_copy = {k: v for k, v in entry.items() if k != "chain_hash"}
                chain_content = json.dumps(entry_copy, sort_keys=True)
                if previous_hash:
                    chain_content = previous_hash + chain_content

                expected_chain = hashlib.sha256(
                    chain_content.encode()
                ).hexdigest()

                if stored_chain != expected_chain:
                    return False

                previous_hash = stored_chain

        return True
```

### Export for Compliance
```python
def export_compliance_package(
    log_dir: str,
    output_file: str,
    start_date: str,
    end_date: str
):
    """Export logs for compliance review."""
    logs = query_logs(log_dir, start_date=start_date, end_date=end_date)
    report = generate_audit_report(log_dir)

    package = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "period": {"start": start_date, "end": end_date},
        "summary": report,
        "logs": logs
    }

    with open(output_file, 'w') as f:
        json.dump(package, f, indent=2)

    return output_file
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
