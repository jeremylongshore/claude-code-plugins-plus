---
name: twinmind-sdk-patterns
description: |
  Apply production-ready TwinMind SDK patterns for TypeScript and Python.
  Use when implementing TwinMind integrations, refactoring API usage,
  or establishing team coding standards for meeting AI integration.
  Trigger with phrases like "twinmind SDK patterns", "twinmind best practices",
  "twinmind code patterns", "idiomatic twinmind".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind SDK Patterns

## Overview
Production patterns for TwinMind's AI memory and meeting intelligence REST API. TwinMind captures, organizes, and retrieves contextual memories from conversations and meetings.

## Prerequisites
- TwinMind API key configured
- Understanding of REST API patterns
- Familiarity with memory/context retrieval concepts

## Instructions

### Step 1: Client Wrapper with Authentication

```python
import requests
import os

class TwinMindClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.twinmind.com/v1"):
        self.api_key = api_key or os.environ["TWINMIND_API_KEY"]
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, path: str, **kwargs):
        response = self.session.request(method, f"{self.base_url}{path}", **kwargs)
        response.raise_for_status()
        return response.json()
```

### Step 2: Memory Storage and Retrieval

```python
class TwinMindClient:
    # ... (continued from Step 1)

    def store_memory(self, content: str, context: dict = None, tags: list = None) -> dict:
        return self._request("POST", "/memories", json={
            "content": content,
            "context": context or {},
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat()
        })

    def search_memories(self, query: str, limit: int = 10, tags: list = None) -> list:
        params = {"q": query, "limit": limit}
        if tags:
            params["tags"] = ",".join(tags)
        return self._request("GET", "/memories/search", params=params)

    def get_memory(self, memory_id: str) -> dict:
        return self._request("GET", f"/memories/{memory_id}")
```

### Step 3: Meeting Context Integration

```python
    def create_meeting_context(self, meeting_id: str, transcript: str, participants: list) -> dict:
        return self._request("POST", "/contexts/meeting", json={
            "meeting_id": meeting_id,
            "transcript": transcript,
            "participants": participants,
            "extract_action_items": True,
            "extract_decisions": True
        })

    def get_meeting_insights(self, meeting_id: str) -> dict:
        return self._request("GET", f"/contexts/meeting/{meeting_id}/insights")
```

### Step 4: Batch Operations with Rate Limiting

```python
import time

def batch_store_memories(client: TwinMindClient, memories: list, batch_size: int = 20):
    results = []
    for i in range(0, len(memories), batch_size):
        batch = memories[i:i+batch_size]
        for memory in batch:
            try:
                result = client.store_memory(**memory)
                results.append({"status": "ok", "id": result["id"]})
            except requests.HTTPError as e:
                if e.response.status_code == 429:  # HTTP 429 Too Many Requests
                    time.sleep(int(e.response.headers.get("Retry-After", 5)))
                    result = client.store_memory(**memory)
                    results.append({"status": "ok", "id": result["id"]})
                else:
                    results.append({"status": "error", "error": str(e)})
        time.sleep(1)  # rate limit between batches
    return results
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Verify `TWINMIND_API_KEY` |
| `429 Rate Limited` | Too many requests | Respect `Retry-After` header |
| `404 Not Found` | Invalid memory/meeting ID | Validate IDs before lookup |
| Empty search results | Query too specific | Broaden query terms |

## Examples

### Full Meeting Workflow
```python
client = TwinMindClient()
# After meeting ends
ctx = client.create_meeting_context(
    meeting_id="mtg-123",
    transcript=transcript_text,
    participants=["alice@co.com", "bob@co.com"]
)
insights = client.get_meeting_insights("mtg-123")
for item in insights.get("action_items", []):
    print(f"- [{item['assignee']}] {item['task']}")
```

## Resources
- [TwinMind API](https://docs.twinmind.com)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale