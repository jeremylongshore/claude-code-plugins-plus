---
name: grammarly-core-workflow-a
description: |
  Execute Grammarly primary workflow: Core Workflow A.
  Use when implementing primary use case,
  building main features, or core integration tasks.
  Trigger with phrases like "grammarly main workflow",
  "primary task with grammarly".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing, scoring]
compatible-with: claude-code
---

# Grammarly Writing Score Integration

## Overview

Integrate Grammarly's Writing Score API into your application. Score documents, track writing quality over time, and provide feedback. The API evaluates text across four dimensions: engagement, correctness, clarity, and tone.

## Prerequisites

- Completed `grammarly-install-auth` setup
- Understanding of score dimensions

## Instructions

### Step 1: Typed Score Client

```typescript
// src/grammarly/scoring.ts
interface WritingScore {
  overallScore: number;
  engagement: number;
  correctness: number;
  clarity: number;
  tone: number;
}

interface ScoreRequest {
  text: string;
  audienceType?: 'general' | 'knowledgeable' | 'expert';
  domain?: 'academic' | 'business' | 'general' | 'email' | 'casual';
}

async function scoreDocument(req: ScoreRequest, token: string): Promise<WritingScore> {
  const response = await fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) throw new Error(`Grammarly API ${response.status}: ${await response.text()}`);
  return response.json();
}
```

### Step 2: Batch Document Scoring

```typescript
async function batchScore(documents: string[], token: string): Promise<WritingScore[]> {
  const results: WritingScore[] = [];
  for (const doc of documents) {
    if (doc.split(/\s+/).length < 30) {
      console.warn('Skipping: minimum 30 words required');
      continue;
    }
    const score = await scoreDocument({ text: doc }, token);
    results.push(score);
    await new Promise(r => setTimeout(r, 500)); // Rate limit buffer
  }
  return results;
}
```

### Step 3: Quality Threshold Enforcement

```typescript
interface QualityGate {
  minOverall: number;
  minCorrectness: number;
  minClarity: number;
}

function checkQualityGate(score: WritingScore, gate: QualityGate): { passed: boolean; issues: string[] } {
  const issues: string[] = [];
  if (score.overallScore < gate.minOverall) issues.push(`Overall ${score.overallScore} < ${gate.minOverall}`);
  if (score.correctness < gate.minCorrectness) issues.push(`Correctness ${score.correctness} < ${gate.minCorrectness}`);
  if (score.clarity < gate.minClarity) issues.push(`Clarity ${score.clarity} < ${gate.minClarity}`);
  return { passed: issues.length === 0, issues };
}

// Usage: enforce quality before publishing
const score = await scoreDocument({ text: blogPost }, token);
const gate = checkQualityGate(score, { minOverall: 80, minCorrectness: 90, minClarity: 75 });
if (!gate.passed) console.error('Quality gate failed:', gate.issues);
```

## API Limits

| Limit | Value |
|-------|-------|
| Max text size | 4 MB |
| Max characters | 100,000 |
| Min words | 30 |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400` | Text too short | Ensure >= 30 words |
| `413` | Text too large | Split into chunks < 100K chars |
| `429` | Rate limited | Implement exponential backoff |

## Resources

- [Writing Score API](https://developer.grammarly.com/writing-score-api.html)
- [Score Dimensions](https://developer.grammarly.com/)

## Next Steps

For AI and plagiarism detection, see `grammarly-core-workflow-b`.
