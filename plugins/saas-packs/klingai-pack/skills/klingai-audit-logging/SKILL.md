---
name: klingai-audit-logging
description: |
  Implement comprehensive audit logging for Kling AI operations. Use when tracking API usage,
  compliance requirements, or security audits. Trigger with phrases like 'klingai audit',
  'kling ai logging', 'klingai compliance log', 'video generation audit trail'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Audit Logging

## Overview

This skill demonstrates implementing comprehensive audit logging for Kling AI operations including API calls, user actions, security events, and compliance-ready logs.

## Prerequisites

- Kling AI API key configured
- Log storage (file, database, or cloud logging)
- Python 3.8+

## Instructions

Follow these steps for audit logging:

1. **Define Events**: Identify what to log
2. **Create Logger**: Implement logging infrastructure
3. **Capture Context**: Include all relevant metadata
4. **Store Securely**: Use tamper-evident storage
5. **Enable Search**: Make logs queryable

## Audit Event Types

```
Audit Event Categories:

AUTHENTICATION:
- api_key_used
- api_key_rotated
- access_denied

API OPERATIONS:
- video_generation_started
- video_generation_completed
- video_generation_failed
- video_downloaded
- video_deleted

USER ACTIONS:
- prompt_submitted
- settings_changed
- quota_checked

ADMIN ACTIONS:
- user_added
- user_removed
- budget_modified
- policy_updated

SECURITY EVENTS:
- rate_limit_exceeded
- suspicious_activity
- policy_violation
```

## Audit Logger Implementation

```python
import json
import hashlib
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
import os

class AuditEventType(Enum):
    # Authentication
    API_KEY_USED = "api_key_used"
    ACCESS_DENIED = "access_denied"

    # Operations
    GENERATION_STARTED = "generation_started"
    GENERATION_COMPLETED = "generation_completed"
    GENERATION_FAILED = "generation_failed"
    VIDEO_DOWNLOADED = "video_downloaded"

    # User Actions
    PROMPT_SUBMITTED = "prompt_submitted"
    SETTINGS_CHANGED = "settings_changed"

    # Admin
    USER_ADDED = "user_added"
    BUDGET_MODIFIED = "budget_modified"

    # Security
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    POLICY_VIOLATION = "policy_violation"

@dataclass
class AuditEvent:
    event_id: str
    timestamp: str
    event_type: str
    actor_id: str
    actor_type: str  # user, system, admin
    resource_type: str
    resource_id: Optional[str]
    action: str
    outcome: str  # success, failure, blocked
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Dict[str, Any]
    checksum: Optional[str] = None

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate tamper-evident checksum."""
        data = f"{self.event_id}:{self.timestamp}:{self.event_type}:{self.actor_id}:{self.action}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

class AuditLogger:
    """Comprehensive audit logging for Kling AI operations."""

    def __init__(
        self,
        log_file: str = "audit.log",
        json_file: str = "audit.json",
        include_pii: bool = False
    ):
        self.log_file = log_file
        self.json_file = json_file
        self.include_pii = include_pii
        self.events: List[AuditEvent] = []
        self._setup_logger()

    def _setup_logger(self):
        """Set up file logger."""
        self.logger = logging.getLogger("klingai.audit")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        ))
        self.logger.addHandler(handler)

    def log(
        self,
        event_type: AuditEventType,
        actor_id: str,
        resource_type: str,
        action: str,
        outcome: str = "success",
        resource_id: str = None,
        actor_type: str = "user",
        ip_address: str = None,
        user_agent: str = None,
        **metadata
    ) -> AuditEvent:
        """Log an audit event."""
        import uuid

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type.value,
            actor_id=self._mask_if_pii(actor_id),
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            ip_address=self._mask_ip(ip_address) if ip_address else None,
            user_agent=user_agent,
            metadata=self._sanitize_metadata(metadata)
        )

        self.events.append(event)
        self._write_event(event)

        return event

    def _mask_if_pii(self, value: str) -> str:
        """Mask PII if not including in logs."""
        if self.include_pii:
            return value
        if "@" in value:  # Email
            parts = value.split("@")
            return f"{parts[0][:2]}***@{parts[1]}"
        return value

    def _mask_ip(self, ip: str) -> str:
        """Mask IP address."""
        if self.include_pii:
            return ip
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        return "xxx.xxx.xxx.xxx"

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Remove sensitive data from metadata."""
        sensitive_keys = ["api_key", "password", "token", "secret"]
        return {
            k: "***REDACTED***" if any(s in k.lower() for s in sensitive_keys) else v
            for k, v in metadata.items()
        }

    def _write_event(self, event: AuditEvent):
        """Write event to log files."""
        # Text log
        self.logger.info(
            f"{event.event_type} | {event.actor_id} | {event.action} | {event.outcome}"
        )

        # JSON log (append)
        with open(self.json_file, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def query(
        self,
        event_type: AuditEventType = None,
        actor_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        outcome: str = None
    ) -> List[AuditEvent]:
        """Query audit events."""
        results = self.events

        if event_type:
            results = [e for e in results if e.event_type == event_type.value]
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time.isoformat()]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time.isoformat()]

        return results

    def get_user_activity(self, actor_id: str, days: int = 30) -> Dict:
        """Get user activity summary."""
        from datetime import timedelta

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        user_events = [
            e for e in self.events
            if e.actor_id == actor_id and e.timestamp >= cutoff
        ]

        return {
            "actor_id": actor_id,
            "period_days": days,
            "total_events": len(user_events),
            "by_type": self._count_by_type(user_events),
            "by_outcome": self._count_by_outcome(user_events),
            "last_activity": max(e.timestamp for e in user_events) if user_events else None
        }

    def _count_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return counts

    def _count_by_outcome(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by outcome."""
        counts = {}
        for e in events:
            counts[e.outcome] = counts.get(e.outcome, 0) + 1
        return counts

    def verify_integrity(self) -> Dict:
        """Verify log integrity using checksums."""
        valid = 0
        invalid = 0

        for event in self.events:
            expected = event._calculate_checksum()
            if event.checksum == expected:
                valid += 1
            else:
                invalid += 1

        return {
            "total": len(self.events),
            "valid": valid,
            "invalid": invalid,
            "integrity_ok": invalid == 0
        }
```

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

## Output

Successful execution produces:
- Timestamped audit events
- Tamper-evident checksums
- User activity summaries
- Compliance-ready logs

## Error Handling

Common errors and solutions:
1. **Log Write Failed**: Check file permissions
2. **Checksum Mismatch**: Investigate tampering
3. **Missing Events**: Verify all paths log

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Audit Logging Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [SOC 2 Logging Requirements](https://www.aicpa.org/soc)
- [GDPR Audit Requirements](https://gdpr.eu/article-30-records-of-processing-activities/)
