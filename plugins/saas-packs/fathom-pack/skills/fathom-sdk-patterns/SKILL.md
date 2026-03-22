---
name: fathom-sdk-patterns
description: |
  Production-ready Fathom API client patterns in Python and TypeScript.
  Use when building reusable Fathom clients, implementing meeting data pipelines,
  or wrapping the Fathom REST API.
  Trigger with phrases like "fathom API patterns", "fathom client wrapper",
  "fathom Python client", "fathom TypeScript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom SDK Patterns

## Python Client

```python
import os, requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class FathomConfig:
    api_key: str
    base_url: str = "https://api.fathom.ai/external/v1"
    timeout: int = 30

class FathomClient:
    def __init__(self, config: Optional[FathomConfig] = None):
        self.config = config or FathomConfig(api_key=os.environ["FATHOM_API_KEY"])
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": self.config.api_key})

    def list_meetings(self, limit: int = 20, **filters) -> list[dict]:
        params = {"limit": limit, **filters}
        resp = self.session.get(f"{self.config.base_url}/meetings", params=params, timeout=self.config.timeout)
        resp.raise_for_status()
        return resp.json().get("meetings", [])

    def get_transcript(self, recording_id: str) -> dict:
        resp = self.session.get(f"{self.config.base_url}/recordings/{recording_id}/transcript", timeout=self.config.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_summary(self, recording_id: str) -> dict:
        resp = self.session.get(f"{self.config.base_url}/recordings/{recording_id}/summary", timeout=self.config.timeout)
        resp.raise_for_status()
        return resp.json()
```

## TypeScript Client

```typescript
class FathomClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey ?? process.env.FATHOM_API_KEY!;
    this.baseUrl = "https://api.fathom.ai/external/v1";
  }

  private async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    const resp = await fetch(url, { headers: { "X-Api-Key": this.apiKey } });
    if (!resp.ok) throw new Error(`Fathom ${resp.status}: ${await resp.text()}`);
    return resp.json();
  }

  async listMeetings(limit = 20) { return this.get<{meetings: any[]}>("/meetings", {limit: String(limit)}); }
  async getTranscript(id: string) { return this.get(`/recordings/${id}/transcript`); }
  async getSummary(id: string) { return this.get(`/recordings/${id}/summary`); }
}
```

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Invalid API key | Regenerate key |
| 404 | Recording not found | Verify recording ID |
| 429 | Rate limited (60/min) | Backoff and retry |

## Resources

- [Fathom API Reference](https://developers.fathom.ai/api-reference)

## Next Steps

Apply in `fathom-core-workflow-a` for meeting analytics.
