---
name: klingai-audit-logging
description: |
  Implement audit logging for Kling AI operations for compliance and security. Use when tracking
  API usage or preparing for audits. Trigger with phrases like 'klingai audit', 'kling ai audit log',
  'klingai compliance log', 'video generation audit trail'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, audit, compliance, logging]

---
# Kling AI Audit Logging

## Overview

Compliance-grade audit logging for Kling AI API operations. Every task submission, status change, and credential usage is captured in tamper-evident structured logs.

## Audit Event Schema

```python
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path

class AuditLogger:
    """Append-only audit log with integrity checksums."""

    def __init__(self, log_dir: str = "audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._prev_hash = "genesis"

    def _compute_hash(self, entry: dict) -> str:
        raw = json.dumps(entry, sort_keys=True) + self._prev_hash
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def log(self, event_type: str, actor: str, details: dict):
        """Write a tamper-evident audit entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "actor": actor,
            "details": details,
            "prev_hash": self._prev_hash,
        }
        entry["hash"] = self._compute_hash(entry)
        self._prev_hash = entry["hash"]

        date = datetime.utcnow().strftime("%Y-%m-%d")
        filepath = self.log_dir / f"audit-{date}.jsonl"
        with open(filepath, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry["hash"]
```

## Audit Events for Kling AI

```python
class KlingAuditClient:
    """Kling client with full audit trail."""

    def __init__(self, base_client, audit: AuditLogger, actor: str = "system"):
        self.client = base_client
        self.audit = audit
        self.actor = actor

    def text_to_video(self, prompt: str, **kwargs):
        # Log submission
        self.audit.log("task_submitted", self.actor, {
            "action": "text_to_video",
            "model": kwargs.get("model", "kling-v2-master"),
            "duration": kwargs.get("duration", 5),
            "mode": kwargs.get("mode", "standard"),
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
            "prompt_length": len(prompt),
        })

        result = self.client.text_to_video(prompt, **kwargs)

        # Log completion
        self.audit.log("task_completed", self.actor, {
            "action": "text_to_video",
            "status": "succeed",
            "video_count": len(result.get("videos", [])),
        })

        return result

    def log_auth_event(self, event: str, success: bool):
        self.audit.log("auth_event", self.actor, {
            "event": event,
            "success": success,
            "access_key_prefix": self.client.config.access_key[:8] + "...",
        })
```

## Audit Log Verification

```python
def verify_audit_chain(log_file: str) -> bool:
    """Verify tamper-evidence of audit log chain."""
    prev_hash = "genesis"
    entries = []

    with open(log_file) as f:
        for line_num, line in enumerate(f, 1):
            entry = json.loads(line)
            entries.append(entry)

            if entry["prev_hash"] != prev_hash:
                print(f"Chain broken at line {line_num}: "
                      f"expected prev_hash={prev_hash}, got {entry['prev_hash']}")
                return False

            # Recompute hash
            check_entry = {k: v for k, v in entry.items() if k != "hash"}
            raw = json.dumps(check_entry, sort_keys=True) + prev_hash
            expected_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

            if entry["hash"] != expected_hash:
                print(f"Hash mismatch at line {line_num}")
                return False

            prev_hash = entry["hash"]

    print(f"Verified {len(entries)} entries -- chain intact")
    return True
```

## Audit Report Generator

```python
def generate_audit_report(log_dir: str = "audit", days: int = 30) -> dict:
    """Generate compliance audit report."""
    from collections import Counter
    from datetime import timedelta

    log_path = Path(log_dir)
    events = []

    cutoff = datetime.utcnow() - timedelta(days=days)
    for filepath in sorted(log_path.glob("audit-*.jsonl")):
        with open(filepath) as f:
            for line in f:
                entry = json.loads(line)
                if entry["timestamp"] >= cutoff.isoformat():
                    events.append(entry)

    event_types = Counter(e["event_type"] for e in events)
    actors = Counter(e["actor"] for e in events)

    report = {
        "period_days": days,
        "total_events": len(events),
        "event_types": dict(event_types),
        "unique_actors": len(actors),
        "actors": dict(actors),
        "first_event": events[0]["timestamp"] if events else None,
        "last_event": events[-1]["timestamp"] if events else None,
    }

    print(f"\n=== Audit Report ({days} days) ===")
    print(f"Total events: {report['total_events']}")
    for event_type, count in event_types.most_common():
        print(f"  {event_type}: {count}")
    print(f"Actors: {', '.join(actors.keys())}")

    return report
```

## Compliance Checklist

- [ ] All API calls logged with timestamp, actor, action
- [ ] Prompts stored as hashes (not plaintext) for privacy
- [ ] Audit chain integrity verifiable
- [ ] Logs retained for required period (typically 1-7 years)
- [ ] Log access restricted to authorized personnel
- [ ] Regular verification of chain integrity

## Resources

- [Developer Portal](https://app.klingai.com/global/dev)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
