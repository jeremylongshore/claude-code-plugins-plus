---
name: grammarly-core-workflow-b
description: |
  Execute Grammarly secondary workflow: Core Workflow B.
  Use when implementing secondary use case,
  or complementing primary workflow.
  Trigger with phrases like "grammarly secondary workflow",
  "secondary task with grammarly".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing, ai-detection]
compatible-with: claude-code
---

# Grammarly AI & Plagiarism Detection

## Overview

Detect AI-generated content and check for plagiarism using Grammarly's detection APIs. AI Detection returns a score (0-100) indicating likelihood of AI generation. Plagiarism Detection compares text against billions of web pages and academic papers.

## Instructions

### Step 1: AI Detection Pipeline

```typescript
interface AIDetectionResult { score: number; status: string; }

async function detectAI(text: string, token: string): Promise<AIDetectionResult> {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v1/ai-detection', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  return response.json();
}

// Batch check multiple documents
async function batchAIDetection(documents: Array<{ id: string; text: string }>, token: string) {
  const results = [];
  for (const doc of documents) {
    const result = await detectAI(doc.text, token);
    results.push({ ...doc, aiScore: result.score, isLikelyAI: result.score > 70 });
    await new Promise(r => setTimeout(r, 500));
  }
  return results;
}
```

### Step 2: Plagiarism Detection (Async)

```typescript
async function checkPlagiarism(text: string, token: string) {
  // Create request
  const createRes = await fetch('https://api.grammarly.com/ecosystem/api/v1/plagiarism', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  const { id } = await createRes.json();

  // Poll for results (async processing)
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 3000));
    const statusRes = await fetch(`https://api.grammarly.com/ecosystem/api/v1/plagiarism/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const result = await statusRes.json();
    if (result.status !== 'pending') return result;
  }
  throw new Error('Plagiarism check timed out');
}
```

### Step 3: Combined Content Quality Pipeline

```typescript
async function fullContentAudit(text: string, token: string) {
  const [score, ai, plagiarism] = await Promise.all([
    scoreDocument({ text }, token),
    detectAI(text, token),
    checkPlagiarism(text, token),
  ]);

  return {
    writingScore: score.overallScore,
    correctness: score.correctness,
    clarity: score.clarity,
    aiLikelihood: ai.score,
    plagiarismScore: plagiarism.score,
    plagiarismMatches: plagiarism.matches?.length || 0,
    passed: score.overallScore >= 70 && ai.score < 50 && plagiarism.score < 20,
  };
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400` text too short | < 30 words | Ensure minimum length |
| Poll timeout | Processing taking long | Increase poll duration |
| AI score inconsistent | Short text | AI detection works best on 200+ words |

## Resources

- [AI Detection API](https://developer.grammarly.com/ai-detection-api.html)
- [Plagiarism Detection API](https://developer.grammarly.com/plagiarism-detection-api.html)

## Next Steps

For common errors, see `grammarly-common-errors`.
