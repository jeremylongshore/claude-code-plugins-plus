# Example MCP Tool Payloads

## 1. store_session_to_cascade

Store a session from CASS to Cascade with redaction, encryption, and indexing.

```json
{
  "session_id": "cass_session_123",
  "tags": ["deployment", "aws", "production"],
  "metadata": {
    "project": "api-gateway",
    "team": "platform"
  },
  "mode": "mock"
}
```

**Response:**
```json
{
  "ok": true,
  "session_id": "cass_session_123",
  "cascade_uri": "cascade://sha256:dfc469cddb8fa9507792ef16f968932535a001aa377dd42075426fdc3bf61750",
  "indexed": true,
  "redaction": {
    "rules_fired": [
      {
        "rule": "aws_access_key",
        "count": 1
      },
      {
        "rule": "email",
        "count": 2
      }
    ]
  },
  "crypto": {
    "enc": "AES-256-GCM",
    "key_id": "default",
    "plaintext_sha256": "abc123...",
    "ciphertext_sha256": "def456...",
    "bytes": 4567
  },
  "memory_card": {
    "title": "Deploy API to production",
    "summary_bullets": [
      "user: Deploy the API to us-east-1 using my credentials...",
      "assistant: I'll help with the deployment...",
      "user: Great, send notifications to john@example.com"
    ],
    "decisions": [
      "Decided to use ECS for container orchestration"
    ],
    "todos": [
      "Need to configure CloudWatch monitoring",
      "Should set up auto-scaling policies"
    ],
    "entities": ["AWS", "ECS", "CloudWatch", "Production", "API"],
    "keywords": ["deploy", "production", "aws", "ecs", "monitoring"],
    "notable_quotes": [
      "What region should we use?",
      "Perfect! Let's proceed with the deployment."
    ]
  }
}
```

---

## 2. query_memories

Search the local FTS index for memories. **NEVER queries Cascade directly.**

```json
{
  "query": "deploy production aws",
  "tags": ["deployment"],
  "time_range": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-31T23:59:59Z"
  },
  "limit": 10
}
```

**Response:**
```json
{
  "ok": true,
  "hits": [
    {
      "cass_session_id": "cass_session_123",
      "cascade_uri": "cascade://sha256:dfc469...",
      "title": "Deploy API to production",
      "snippet": "Deploy API to production - User requested deployment to AWS...",
      "tags": ["deployment", "aws", "production"],
      "created_at": "2025-01-15T10:30:00Z",
      "score": 2.456
    },
    {
      "cass_session_id": "cass_session_789",
      "cascade_uri": "cascade://sha256:ef789a...",
      "title": "Production database migration",
      "snippet": "Production database migration - Discussed migrating RDS instance...",
      "tags": ["deployment", "database"],
      "created_at": "2025-01-12T14:20:00Z",
      "score": 1.823
    }
  ]
}
```

**Simple query (minimal params):**
```json
{
  "query": "api deployment"
}
```

---

## 3. retrieve_session_from_cascade

Fetch and decrypt a session from Cascade using its URI.

```json
{
  "cascade_uri": "cascade://sha256:dfc469cddb8fa9507792ef16f968932535a001aa377dd42075426fdc3bf61750",
  "mode": "mock"
}
```

**Response:**
```json
{
  "ok": true,
  "cascade_uri": "cascade://sha256:dfc469...",
  "session": {
    "session_id": "cass_session_123",
    "messages": [
      {
        "role": "user",
        "content": "Deploy the API using [REDACTED:AWS_ACCESS_KEY]",
        "timestamp": "2025-01-15T10:30:00Z"
      },
      {
        "role": "assistant",
        "content": "I'll help deploy the API. What region?",
        "timestamp": "2025-01-15T10:30:15Z"
      },
      {
        "role": "user",
        "content": "us-east-1, email [REDACTED:EMAIL] for alerts",
        "timestamp": "2025-01-15T10:31:00Z"
      }
    ],
    "metadata": {
      "started_at": "2025-01-15T10:30:00Z",
      "ended_at": "2025-01-15T10:35:00Z"
    }
  },
  "memory_card": {
    "title": "Deploy API to production",
    "summary_bullets": ["..."],
    "decisions": ["Decided to use ECS"],
    "todos": ["Configure monitoring"],
    "entities": ["AWS", "ECS"],
    "keywords": ["deploy", "production"],
    "notable_quotes": ["What region?"]
  },
  "crypto": {
    "verified": true,
    "plaintext_sha256": "abc123...",
    "ciphertext_sha256": "def456...",
    "key_id": "default"
  }
}
```

---

## 4. estimate_storage_cost

Estimate Cascade storage costs for a given data size.

```json
{
  "bytes": 4567,
  "redundancy": 3,
  "pricing_inputs": {
    "storage_per_gb_month": 0.02,
    "request_per_1k": 0.0004
  }
}
```

**Response:**
```json
{
  "ok": true,
  "bytes": 4567,
  "gb": 0.000004,
  "monthly_storage_usd": 0.0002,
  "estimated_request_usd": 0.0001,
  "total_estimated_usd": 0.0003,
  "assumptions": {
    "redundancy": 3,
    "storage_per_gb_month_usd": 0.02,
    "request_per_1k_usd": 0.0004,
    "estimated_reads_per_month": 100
  }
}
```

**Minimal params:**
```json
{
  "bytes": 10000
}
```

---

## Error Responses

All tools return `{"ok": false, "error": "..."}` on failure.

### Example: Critical pattern detected
```json
{
  "ok": false,
  "error": "CRITICAL: Detected private_key pattern in session data. Cannot safely store to Cascade. Found 1 occurrence(s). Remove sensitive data from source CASS session before storing."
}
```

### Example: Live mode not configured
```json
{
  "ok": false,
  "error": "Live Cascade mode not configured. Required: LUMERA_CASCADE_ENDPOINT and LUMERA_CASCADE_API_KEY environment variables. Use mode='mock' for local testing."
}
```

### Example: URI not found
```json
{
  "ok": false,
  "error": "URI not found in local index"
}
```
