---
name: grammarly-hello-world
description: |
  Create a minimal working Grammarly example.
  Use when starting a new Grammarly integration, testing your setup,
  or learning basic Grammarly API patterns.
  Trigger with phrases like "grammarly hello world", "grammarly example",
  "grammarly quick start", "simple grammarly code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Hello World

## Overview

Score a text document using Grammarly's Writing Score API. Returns an overall score plus sub-scores for engagement, correctness, tone, and clarity.

## Prerequisites

- Completed `grammarly-install-auth` setup
- Valid access token with `scores-api:read` scope

## Instructions

### Step 1: Score a Document

```typescript
// hello-grammarly.ts
import 'dotenv/config';

const TOKEN = process.env.GRAMMARLY_ACCESS_TOKEN!;

async function scoreText(text: string) {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  const result = await response.json();
  console.log('Overall Score:', result.overallScore);
  console.log('Engagement:', result.engagement);
  console.log('Correctness:', result.correctness);
  console.log('Clarity:', result.clarity);
  console.log('Tone:', result.tone);
  return result;
}

scoreText('Their going to the store tommorow to buy there supplys for the trip.').catch(console.error);
```

### Step 2: AI Detection

```typescript
async function detectAI(text: string) {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v1/ai-detection', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });
  const result = await response.json();
  console.log('AI Score:', result.score); // 0-100, higher = more likely AI
  return result;
}
```

### Step 3: Plagiarism Detection

```typescript
async function checkPlagiarism(text: string) {
  // Step 1: Create score request
  const createRes = await fetch('https://api.grammarly.com/ecosystem/api/v1/plagiarism', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  const { id } = await createRes.json();

  // Step 2: Poll for results
  let result;
  do {
    await new Promise(r => setTimeout(r, 3000));
    const statusRes = await fetch(`https://api.grammarly.com/ecosystem/api/v1/plagiarism/${id}`, {
      headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    result = await statusRes.json();
  } while (result.status === 'pending');

  console.log('Plagiarism score:', result.score);
  console.log('Matches:', result.matches?.length || 0);
  return result;
}
```

### Step 4: curl Quick Test

```bash
curl -X POST https://api.grammarly.com/ecosystem/api/v2/scores \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test sentence."}' | python3 -m json.tool
```

## Output

- Writing score with engagement, correctness, clarity, and tone breakdown
- AI detection score (0-100)
- Plagiarism detection with source matches

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Token expired | Re-authenticate |
| `400 Bad Request` | Text too short (< 30 words) | Minimum 30 words required |
| `413 Payload Too Large` | Text > 100,000 characters | Split into chunks |
| `429 Rate Limited` | Too many requests | Implement backoff |

## Resources

- [Writing Score API](https://developer.grammarly.com/writing-score-api.html)
- [AI Detection API](https://developer.grammarly.com/ai-detection-api.html)
- [Plagiarism Detection API](https://developer.grammarly.com/plagiarism-detection-api.html)

## Next Steps

Proceed to `grammarly-local-dev-loop` for development workflow.
