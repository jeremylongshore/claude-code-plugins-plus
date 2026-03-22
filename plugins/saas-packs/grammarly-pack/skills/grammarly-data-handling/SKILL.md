---
name: grammarly-data-handling
description: |
  Implement Grammarly data handling patterns for document processing.
  Use when handling large documents, managing text chunking,
  or implementing data pipelines for Grammarly API.
  Trigger with phrases like "grammarly data", "grammarly documents",
  "grammarly text processing", "grammarly pipeline".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Data Handling

## Overview

Handle large documents, text chunking, and data pipelines for Grammarly API. The API accepts max 100,000 characters (4 MB) with a minimum of 30 words.

## Instructions

### Step 1: Text Chunking

```typescript
function chunkText(text: string, maxChars = 90000): string[] {
  if (text.length <= maxChars) return [text];
  const paragraphs = text.split('\n\n');
  const chunks: string[] = [];
  let current = '';
  for (const p of paragraphs) {
    if ((current + '\n\n' + p).length > maxChars && current) {
      chunks.push(current);
      current = p;
    } else {
      current = current ? current + '\n\n' + p : p;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}
```

### Step 2: Aggregate Scores Across Chunks

```typescript
function aggregateScores(scores: any[]): any {
  const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
  return {
    overallScore: Math.round(avg(scores.map(s => s.overallScore))),
    correctness: Math.round(avg(scores.map(s => s.correctness))),
    clarity: Math.round(avg(scores.map(s => s.clarity))),
    engagement: Math.round(avg(scores.map(s => s.engagement))),
    tone: Math.round(avg(scores.map(s => s.tone))),
    chunkCount: scores.length,
  };
}
```

### Step 3: File Processing Pipeline

```typescript
import fs from 'fs';

async function scoreFile(filePath: string, token: string) {
  const text = fs.readFileSync(filePath, 'utf-8');
  const chunks = chunkText(text);
  const scores = [];
  for (const chunk of chunks) {
    if (chunk.split(/\s+/).length >= 30) {
      scores.push(await grammarlyClient.score(chunk));
    }
  }
  return aggregateScores(scores);
}
```

## Resources

- [Writing Score API](https://developer.grammarly.com/writing-score-api.html)
