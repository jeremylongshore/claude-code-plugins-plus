---
name: lindy-sdk-patterns
description: |
  Lindy AI integration patterns for webhook handling, HTTP actions, and Run Code.
  Use when building integrations, calling Lindy agents from code,
  or implementing the Run Code action with Python/JavaScript.
  Trigger with phrases like "lindy SDK patterns", "lindy best practices",
  "lindy API patterns", "lindy Run Code", "lindy HTTP Request".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, api]

---
# Lindy SDK & Integration Patterns

## Overview
Lindy is primarily a no-code platform. External integration happens through three
channels: **Webhook triggers** (inbound), **HTTP Request actions** (outbound), and
**Run Code actions** (inline Python/JS execution via E2B sandbox). This skill covers
patterns for each.

## Prerequisites
- Lindy account with active agents
- Node.js 18+ or Python 3.10+ for webhook receivers
- Completed `lindy-install-auth` setup

## Pattern 1: Webhook Trigger Integration
Your application fires webhooks to wake Lindy agents:

```typescript
// lindy-client.ts — Reusable Lindy webhook trigger client
class LindyClient {
  private webhookUrl: string;
  private secret: string;

  constructor(webhookUrl: string, secret: string) {
    this.webhookUrl = webhookUrl;
    this.secret = secret;
  }

  async trigger(payload: Record<string, unknown>): Promise<{ status: number }> {
    const response = await fetch(this.webhookUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.secret}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Lindy webhook failed: ${response.status} ${response.statusText}`);
    }

    return { status: response.status };
  }

  async triggerWithCallback(
    payload: Record<string, unknown>,
    callbackUrl: string
  ): Promise<{ status: number }> {
    return this.trigger({ ...payload, callbackUrl });
  }
}

// Usage
const lindy = new LindyClient(
  'https://public.lindy.ai/api/v1/webhooks/YOUR_ID',
  process.env.LINDY_WEBHOOK_SECRET!
);

await lindy.trigger({ event: 'lead.created', name: 'Jane Doe', email: 'jane@co.com' });
```

## Pattern 2: HTTP Request Action (Agent Calling Your API)
Configure a Lindy agent to call your API as an action step:

**In Lindy Dashboard** — Add HTTP Request action:
- **Method**: POST
- **URL**: `https://api.yourapp.com/process`
- **Headers**: `Authorization: Bearer {{your_api_key}}`, `Content-Type: application/json`
- **Body** (AI Prompt mode):
  ```
  Send the processed data as JSON with fields matching the API schema.
  Include: name from {{trigger.data.name}}, analysis from previous step.
  ```

**Your API endpoint** receives the call:
```typescript
// Your API receiving Lindy agent calls
app.post('/process', async (req, res) => {
  const { name, analysis } = req.body;
  const result = await processData(name, analysis);
  res.json({ result, processedAt: new Date().toISOString() });
});
```

## Pattern 3: Run Code Action (E2B Sandbox)
Execute Python or JavaScript directly in Lindy workflows. Code runs in isolated
Firecracker microVMs with ~150ms startup time.

**Python example** (data transformation in a workflow):
```python
# Run Code action — Python
# Input variables: raw_data (string from previous step)
import json

data = json.loads(raw_data)  # Input vars are always strings

# Process
cleaned = [
    {"name": item["name"].strip(), "score": float(item["score"])}
    for item in data["items"]
    if float(item["score"]) > 0.5
]

# Sort by score descending
cleaned.sort(key=lambda x: x["score"], reverse=True)

# Return value accessible as {{run_code.result}} in next step
return json.dumps({"filtered_count": len(cleaned), "items": cleaned})
```

**JavaScript example** (API call + processing):
```javascript
// Run Code action — JavaScript
// Input variables: query (string), api_key (string)
const response = await fetch(`https://api.example.com/search?q=${query}`, {
  headers: { 'Authorization': `Bearer ${api_key}` }
});
const data = await response.json();

const summary = data.results.map(r => `${r.title}: ${r.snippet}`).join('\n');
return JSON.stringify({ count: data.results.length, summary });
```

**Run Code outputs** (available to subsequent steps):
| Output | Contents |
|--------|----------|
| `{{run_code.result}}` | Value from `return` statement |
| `{{run_code.text}}` | stdout from `print()` / `console.log()` |
| `{{run_code.stderr}}` | Error output for debugging |

**Available Python libraries**: pandas, numpy, scipy, scikit-learn, matplotlib,
requests, aiohttp, beautifulsoup4, nltk, spacy, openpyxl, python-docx

**Key constraint**: All input variables arrive as strings. Cast explicitly:
`count = int(count_str)`, `data = json.loads(json_str)`

## Pattern 4: Callback Pattern (Async Two-Way)
Send a `callbackUrl` in your webhook payload. Lindy can respond back using
the **Send POST Request to Callback** action:

```typescript
// Your app triggers Lindy with a callback URL
await lindy.trigger({
  event: 'analyze.request',
  data: { text: 'Analyze this quarterly report...' },
  callbackUrl: 'https://api.yourapp.com/lindy-callback'
});

// Your callback handler receives Lindy's response
app.post('/lindy-callback', (req, res) => {
  const { analysis, sentiment, summary } = req.body;
  saveAnalysis(analysis);
  res.sendStatus(200);
});
```

## Pattern 5: Retry with Exponential Backoff
```typescript
async function triggerWithRetry(
  client: LindyClient,
  payload: Record<string, unknown>,
  maxRetries = 3
): Promise<void> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      await client.trigger(payload);
      return;
    } catch (error: any) {
      if (attempt === maxRetries) throw error;
      const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

## Error Handling

| Pattern | Failure Mode | Solution |
|---------|-------------|----------|
| Webhook trigger | 401 Unauthorized | Verify Bearer token matches dashboard secret |
| HTTP Request action | Target API unreachable | Check URL, verify HTTPS, test with curl |
| Run Code | Timeout | Avoid infinite loops; keep execution under 30s |
| Run Code | Import error | Use only pre-installed libraries (see list above) |
| Callback | Callback URL unreachable | Ensure HTTPS endpoint is publicly accessible |

## Resources
- [Calling Any API](https://www.lindy.ai/academy-lessons/calling-any-api)
- [Run Code Documentation](https://docs.lindy.ai/skills/by-lindy/run-code)
- [Webhooks Documentation](https://docs.lindy.ai/skills/by-lindy/webhooks)

## Next Steps
Proceed to `lindy-core-workflow-a` for full agent creation workflows.
