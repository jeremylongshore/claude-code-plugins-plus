---
name: gamma-hello-world
description: |
  Generate your first Gamma presentation via the API.
  Use when learning the generate-poll-retrieve workflow,
  testing API connectivity, or creating a minimal example.
  Trigger: "gamma hello world", "gamma quick start",
  "first gamma presentation", "gamma example", "gamma test".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, getting-started]

---
# Gamma Hello World

## Overview

Generate your first presentation using Gamma's async Generate API. The workflow is: POST to create a generation, poll for status, then retrieve results (gammaUrl + exportUrl).

## Prerequisites

- Completed `gamma-install-auth` setup
- Valid `GAMMA_API_KEY` environment variable
- Pro account with available credits

## The Generate-Poll-Retrieve Pattern

All Gamma generations are asynchronous:
1. **POST** `/v1.0/generations` — submit content, receive `generationId`
2. **GET** `/v1.0/generations/{generationId}` — poll every 5s until `completed` or `failed`
3. **Result** — `gammaUrl` (view in app) + `exportUrl` (download PDF/PPTX/PNG)

## Instructions

### Minimal curl Example

```bash
# Step 1: Create generation
GENERATION=$(curl -s -X POST \
  "https://public-api.gamma.app/v1.0/generations" \
  -H "X-API-KEY: ${GAMMA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Create a 5-card presentation about the benefits of AI in business",
    "outputFormat": "presentation"
  }')

GEN_ID=$(echo "$GENERATION" | jq -r '.generationId')
echo "Generation started: $GEN_ID"

# Step 2: Poll until complete (every 5 seconds)
while true; do
  STATUS=$(curl -s \
    "https://public-api.gamma.app/v1.0/generations/${GEN_ID}" \
    -H "X-API-KEY: ${GAMMA_API_KEY}")
  STATE=$(echo "$STATUS" | jq -r '.status')
  echo "Status: $STATE"
  [ "$STATE" = "completed" ] || [ "$STATE" = "failed" ] && break
  sleep 5
done

# Step 3: Retrieve results
echo "$STATUS" | jq '{gammaUrl, exportUrl, creditsUsed}'
```

### Node.js / TypeScript Example

```typescript
const GAMMA_BASE = "https://public-api.gamma.app/v1.0";
const headers = {
  "X-API-KEY": process.env.GAMMA_API_KEY!,
  "Content-Type": "application/json",
};

async function generatePresentation(content: string) {
  // Step 1: Create generation
  const createRes = await fetch(`${GAMMA_BASE}/generations`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      content,
      outputFormat: "presentation",
    }),
  });
  if (!createRes.ok) throw new Error(`Create failed: ${createRes.status}`);
  const { generationId } = await createRes.json();
  console.log(`Generation started: ${generationId}`);

  // Step 2: Poll for completion
  while (true) {
    const pollRes = await fetch(`${GAMMA_BASE}/generations/${generationId}`, { headers });
    const result = await pollRes.json();

    if (result.status === "completed") {
      console.log(`View: ${result.gammaUrl}`);
      console.log(`Download: ${result.exportUrl}`);
      console.log(`Credits used: ${result.creditsUsed}`);
      return result;
    }
    if (result.status === "failed") {
      throw new Error(`Generation failed: ${JSON.stringify(result)}`);
    }
    console.log(`Status: ${result.status}...`);
    await new Promise((r) => setTimeout(r, 5000));
  }
}

// Run it
await generatePresentation("Create a 5-card intro to machine learning");
```

### Python Example

```python
import os, time, requests

BASE = "https://public-api.gamma.app/v1.0"
HEADERS = {
    "X-API-KEY": os.environ["GAMMA_API_KEY"],
    "Content-Type": "application/json",
}

def generate_presentation(content: str) -> dict:
    # Step 1: Create
    resp = requests.post(f"{BASE}/generations", headers=HEADERS, json={
        "content": content,
        "outputFormat": "presentation",
    })
    resp.raise_for_status()
    gen_id = resp.json()["generationId"]
    print(f"Generation started: {gen_id}")

    # Step 2: Poll
    while True:
        poll = requests.get(f"{BASE}/generations/{gen_id}", headers=HEADERS)
        result = poll.json()
        if result["status"] == "completed":
            print(f"View: {result['gammaUrl']}")
            print(f"Download: {result['exportUrl']}")
            return result
        if result["status"] == "failed":
            raise Exception(f"Failed: {result}")
        print(f"Status: {result['status']}...")
        time.sleep(5)

generate_presentation("5-card intro to sustainable energy")
```

## Expected Output

```json
{
  "generationId": "gen_abc123",
  "status": "completed",
  "gammaUrl": "https://gamma.app/docs/Benefits-of-AI-abc123",
  "exportUrl": "https://export.gamma.app/gen_abc123.pdf",
  "creditsUsed": 42
}
```

## Output Formats

| `outputFormat` | Result |
|----------------|--------|
| `presentation` | Slide deck (default) |
| `document` | Long-form document |
| `webpage` | Web page |
| `social_post` | Social media content |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 on POST | Bad API key | Verify `X-API-KEY` header |
| 422 on POST | Invalid parameters | Check `content` and `outputFormat` values |
| `status: "failed"` | Generation could not complete | Simplify content or reduce card count |
| Poll timeout | Very large generation | Increase poll duration beyond 2 minutes |

## Resources

- [Generate a Gamma](https://developers.gamma.app/reference/generate-a-gamma)
- [Generate API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [Explore the API](https://developers.gamma.app/get-started/understanding-the-api-options)

## Next Steps

Proceed to `gamma-core-workflow-a` for advanced generation with themes, images, and export options.
