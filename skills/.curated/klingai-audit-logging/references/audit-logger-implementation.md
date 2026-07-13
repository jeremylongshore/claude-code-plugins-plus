# Audit Logger Implementation

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
