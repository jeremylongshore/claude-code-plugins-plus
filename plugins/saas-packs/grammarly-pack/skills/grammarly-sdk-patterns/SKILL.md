---
name: grammarly-sdk-patterns
description: |
  Apply production-ready Grammarly SDK patterns for TypeScript and Python.
  Use when implementing Grammarly integrations, refactoring SDK usage,
  or establishing team coding standards for Grammarly.
  Trigger with phrases like "grammarly SDK patterns", "grammarly best practices",
  "grammarly code patterns", "idiomatic grammarly".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly SDK Patterns

## Overview

Production patterns for Grammarly API: typed client, token management, text chunking for large documents, and Python integration.

## Instructions

### Step 1: Typed API Client

```typescript
class GrammarlyClient {
  private token: string;
  private expiresAt: number = 0;
  private base = 'https://api.grammarly.com/ecosystem/api';

  constructor(private clientId: string, private clientSecret: string) {}

  private async ensureToken() {
    if (Date.now() < this.expiresAt - 60000) return;
    const res = await fetch(`${this.base}/v1/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'client_credentials', client_id: this.clientId, client_secret: this.clientSecret }),
    });
    const { access_token, expires_in } = await res.json();
    this.token = access_token;
    this.expiresAt = Date.now() + expires_in * 1000;
  }

  async score(text: string) {
    await this.ensureToken();
    const res = await fetch(`${this.base}/v2/scores`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    return res.json();
  }

  async detectAI(text: string) {
    await this.ensureToken();
    const res = await fetch(`${this.base}/v1/ai-detection`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    return res.json();
  }
}
```

### Step 2: Text Chunking for Large Documents

```typescript
function chunkText(text: string, maxChars = 90000): string[] {
  if (text.length <= maxChars) return [text];
  const chunks: string[] = [];
  const paragraphs = text.split('\n\n');
  let current = '';
  for (const p of paragraphs) {
    if ((current + '\n\n' + p).length > maxChars) {
      if (current) chunks.push(current);
      current = p;
    } else {
      current = current ? current + '\n\n' + p : p;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}
```

### Step 3: Python Client

```python
import os, requests
from dotenv import load_dotenv

load_dotenv()

class GrammarlyClient:
    BASE = 'https://api.grammarly.com/ecosystem/api'

    def __init__(self):
        self.token = None
        self._authenticate()

    def _authenticate(self):
        r = requests.post(f'{self.BASE}/v1/oauth/token', data={
            'grant_type': 'client_credentials',
            'client_id': os.environ['GRAMMARLY_CLIENT_ID'],
            'client_secret': os.environ['GRAMMARLY_CLIENT_SECRET'],
        })
        self.token = r.json()['access_token']

    def score(self, text: str):
        r = requests.post(f'{self.BASE}/v2/scores',
            headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
            json={'text': text})
        return r.json()
```

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

Apply patterns in `grammarly-core-workflow-a`.
