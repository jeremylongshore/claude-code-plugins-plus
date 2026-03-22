---
name: openrouter-audit-logging
description: |
  Implement audit logging for OpenRouter API calls. Use when building compliance trails, debugging production issues, or tracking model usage. Triggers: 'openrouter audit', 'openrouter logging', 'audit trail openrouter', 'log openrouter requests'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, security, logging, compliance]

---
# OpenRouter Audit Logging

## Overview

Every OpenRouter API call returns a generation ID and metadata that enables comprehensive audit logging. The generation endpoint (`GET /api/v1/generation?id=`) provides exact cost, token counts, provider used, and latency -- data that the initial response doesn't always include. This skill covers structured logging, cost tracking, PII redaction, and compliance-ready audit trails.

## Core: Generation Metadata Retrieval

```python
import os, json, time, hashlib, logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional
import requests
from openai import OpenAI

log = logging.getLogger("openrouter.audit")

@dataclass
class AuditEntry:
    timestamp: str
    generation_id: str
    model_requested: str
    model_used: str          # Actual model served (may differ with fallbacks)
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    latency_ms: float
    status: str              # "success" | "error" | "timeout"
    user_id: str
    prompt_hash: str         # SHA-256 of prompt (not raw content)
    error_code: Optional[str] = None

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://my-app.com",
        "X-Title": "my-app",
    },
)

def audited_completion(
    messages: list[dict],
    model: str = "anthropic/claude-3.5-sonnet",
    user_id: str = "system",
    **kwargs,
) -> tuple:
    """Make a completion request with full audit logging."""
    prompt_text = json.dumps(messages)
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

    start = time.monotonic()
    status = "success"
    error_code = None

    try:
        response = client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
    except Exception as e:
        status = "error"
        error_code = type(e).__name__
        raise
    finally:
        latency = (time.monotonic() - start) * 1000

    # Fetch exact cost from generation endpoint
    gen_data = {}
    try:
        gen = requests.get(
            f"https://openrouter.ai/api/v1/generation?id={response.id}",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            timeout=5,
        ).json()
        gen_data = gen.get("data", {})
    except Exception:
        log.warning(f"Failed to fetch generation metadata for {response.id}")

    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        generation_id=response.id,
        model_requested=model,
        model_used=response.model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_cost=float(gen_data.get("total_cost", 0)),
        latency_ms=round(latency, 1),
        status=status,
        user_id=user_id,
        prompt_hash=prompt_hash,
        error_code=error_code,
    )

    log.info(json.dumps(asdict(entry)))
    return response, entry
```

## Structured Log Storage

```python
import sqlite3

def init_audit_db(db_path: str = "openrouter_audit.db"):
    """Create append-only audit table."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            generation_id TEXT UNIQUE NOT NULL,
            model_requested TEXT NOT NULL,
            model_used TEXT NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_cost REAL,
            latency_ms REAL,
            status TEXT NOT NULL,
            user_id TEXT,
            prompt_hash TEXT,
            error_code TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
    conn.commit()
    return conn

def write_audit(conn: sqlite3.Connection, entry: AuditEntry):
    """Write audit entry to SQLite (append-only)."""
    conn.execute(
        """INSERT OR IGNORE INTO audit_log
           (timestamp, generation_id, model_requested, model_used,
            prompt_tokens, completion_tokens, total_cost, latency_ms,
            status, user_id, prompt_hash, error_code)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (entry.timestamp, entry.generation_id, entry.model_requested,
         entry.model_used, entry.prompt_tokens, entry.completion_tokens,
         entry.total_cost, entry.latency_ms, entry.status, entry.user_id,
         entry.prompt_hash, entry.error_code),
    )
    conn.commit()
```

## PII Redaction Before Logging

```python
import re

PII_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    (r'\bsk-or-v1-[a-zA-Z0-9]+\b', '[API_KEY]'),
    (r'\b(?:\d{4}[- ]?){3}\d{4}\b', '[CARD]'),
]

def redact_pii(text: str) -> str:
    """Scrub PII from text before logging."""
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text
```

## Audit Queries

```sql
-- Daily cost by model
SELECT date(timestamp) as day, model_used,
       COUNT(*) as requests, SUM(total_cost) as cost
FROM audit_log GROUP BY day, model_used ORDER BY day DESC, cost DESC;

-- Error rate by model (last 24h)
SELECT model_requested, COUNT(*) as total,
       SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
       ROUND(100.0 * SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) / COUNT(*), 1) as error_pct
FROM audit_log WHERE timestamp > datetime('now', '-1 day')
GROUP BY model_requested;

-- Top spenders
SELECT user_id, COUNT(*) as requests, SUM(total_cost) as total_cost
FROM audit_log GROUP BY user_id ORDER BY total_cost DESC LIMIT 10;
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Generation endpoint 404 | Generation ID not found or too old | Fetch within 30 minutes of request |
| Duplicate generation_id | Retry wrote same request twice | Use `INSERT OR IGNORE` |
| Missing `total_cost` | Generation still processing | Retry fetch after 1-2 seconds |
| Auth 401 on generation fetch | Wrong API key for that generation | Use same key that made the request |

## Enterprise Considerations

- Log to append-only storage (SQLite WAL mode, S3, or centralized logging) to prevent tampering
- Hash prompts rather than logging raw content to satisfy data residency requirements
- Set log retention policies (90 days for operational, 7 years for financial compliance)
- Ship structured JSON logs to SIEM (Splunk, Datadog, ELK) for real-time alerting
- Use `user_id` field to enable per-user cost attribution and abuse detection
- Index `generation_id` for fast correlation with OpenRouter dashboard

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Generation API](https://openrouter.ai/docs/api/api-reference/generation-queries/query-a-generation) | [Auth/Key Info](https://openrouter.ai/docs/api/reference/authentication)
