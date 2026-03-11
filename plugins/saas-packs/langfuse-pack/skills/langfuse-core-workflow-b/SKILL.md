---
name: langfuse-core-workflow-b
description: |
  Execute Langfuse secondary workflow: Evaluation and scoring.
  Use when implementing LLM evaluation, adding user feedback,
  or setting up automated quality scoring for AI outputs.
  Trigger with phrases like "langfuse evaluation", "langfuse scoring",
  "rate llm outputs", "langfuse feedback", "evaluate ai responses".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse Core Workflow B: Evaluation & Scoring

## Overview
Implement LLM output evaluation and scoring with Langfuse. Covers manual user feedback collection, automated evaluation functions, A/B testing prompts with score comparison, and building evaluation datasets.

## Prerequisites
- Langfuse instance (Cloud or self-hosted)
- Langfuse SDK configured with API keys
- Traces already being collected (see workflow A)
- Understanding of evaluation metrics

## Instructions

### Step 1: Manual User Feedback Scoring
```typescript
import { Langfuse } from 'langfuse';

const langfuse = new Langfuse();

// Score a specific trace with user feedback
async function submitUserFeedback(
  traceId: string,
  rating: 'positive' | 'negative',
  comment?: string
) {
  langfuse.score({
    traceId,
    name: 'user-feedback',
    value: rating === 'positive' ? 1 : 0,
    comment,
  });

  await langfuse.flushAsync();
}

// Score with granular rating (1-5 stars)
async function submitStarRating(
  traceId: string,
  stars: number,
  observationId?: string
) {
  langfuse.score({
    traceId,
    observationId, // Optional: score a specific generation
    name: 'star-rating',
    value: stars / 5, // Normalize to 0-1
    comment: `${stars}/5 stars`,
  });
}
```

### Step 2: Automated Evaluation Functions
```typescript
// Evaluate response quality automatically
function evaluateResponse(response: string, expectedTopics: string[]): number {
  const topicsFound = expectedTopics.filter(topic =>
    response.toLowerCase().includes(topic.toLowerCase())
  );
  return topicsFound.length / expectedTopics.length;
}

function evaluateLength(response: string, minWords: number, maxWords: number): number {
  const wordCount = response.split(/\s+/).length;
  if (wordCount < minWords) return wordCount / minWords;
  if (wordCount > maxWords) return maxWords / wordCount;
  return 1.0;
}

// Score traces automatically after generation
async function autoScore(
  traceId: string,
  generationId: string,
  response: string,
  expectedTopics: string[]
) {
  const topicScore = evaluateResponse(response, expectedTopics);
  const lengthScore = evaluateLength(response, 50, 500);

  langfuse.score({
    traceId,
    observationId: generationId,
    name: 'topic-coverage',
    value: topicScore,
  });

  langfuse.score({
    traceId,
    observationId: generationId,
    name: 'length-quality',
    value: lengthScore,
  });

  await langfuse.flushAsync();
}
```

### Step 3: LLM-as-Judge Evaluation
```typescript
import OpenAI from 'openai';

const openai = new OpenAI();

async function llmJudge(
  question: string,
  response: string,
  criteria: string
): Promise<{ score: number; reasoning: string }> {
  const result = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0,
    messages: [
      {
        role: 'system',
        content: `You are an AI evaluator. Score the response on a scale of 0-10 based on: ${criteria}.
Return JSON: {"score": <number>, "reasoning": "<explanation>"}`,
      },
      {
        role: 'user',
        content: `Question: ${question}\nResponse: ${response}`,
      },
    ],
    response_format: { type: 'json_object' },
  });

  return JSON.parse(result.choices[0].message.content || '{}');
}

// Use with Langfuse scoring
async function judgeAndScore(traceId: string, question: string, response: string) {
  const evaluation = await llmJudge(question, response, 'accuracy, helpfulness, and clarity');

  langfuse.score({
    traceId,
    name: 'llm-judge',
    value: evaluation.score / 10, // Normalize to 0-1
    comment: evaluation.reasoning,
  });
}
```

### Step 4: A/B Prompt Comparison
```typescript
async function comparePrompts(
  testCases: Array<{ input: string; expectedTopics: string[] }>,
  promptA: string,
  promptB: string
) {
  const results = { promptA: { scores: [] as number[] }, promptB: { scores: [] as number[] } };

  for (const testCase of testCases) {
    // Test Prompt A
    const traceA = langfuse.trace({ name: 'ab-test-prompt-a' });
    const genA = traceA.generation({
      name: 'generate',
      input: testCase.input,
      model: 'gpt-4o-mini',
      metadata: { promptVersion: 'A' },
    });

    const responseA = await callLLM(promptA, testCase.input);
    genA.end({ output: responseA });

    const scoreA = evaluateResponse(responseA, testCase.expectedTopics);
    traceA.score({ name: 'topic-coverage', value: scoreA });
    results.promptA.scores.push(scoreA);

    // Test Prompt B
    const traceB = langfuse.trace({ name: 'ab-test-prompt-b' });
    const responseB = await callLLM(promptB, testCase.input);
    const scoreB = evaluateResponse(responseB, testCase.expectedTopics);
    traceB.score({ name: 'topic-coverage', value: scoreB });
    results.promptB.scores.push(scoreB);
  }

  const avgA = results.promptA.scores.reduce((a, b) => a + b, 0) / results.promptA.scores.length;
  const avgB = results.promptB.scores.reduce((a, b) => a + b, 0) / results.promptB.scores.length;

  await langfuse.flushAsync();
  return { promptA: avgA.toFixed(3), promptB: avgB.toFixed(3), winner: avgA > avgB ? 'A' : 'B' };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Scores not appearing | Flush not called | Always call `flushAsync` after scoring |
| Score out of range | Value not normalized | Normalize all scores to 0-1 range |
| LLM judge inconsistent | High temperature | Set temperature to 0 for evaluations |
| Missing trace ID | Score submitted without trace | Ensure trace exists before scoring |

## Examples

### Quick Feedback Widget Integration
```typescript
// API endpoint for frontend feedback
app.post('/api/feedback', async (req, res) => {
  const { traceId, rating, comment } = req.body;
  await submitUserFeedback(traceId, rating, comment);
  res.json({ success: true });
});
```

## Resources
- [Langfuse Scores](https://langfuse.com/docs/scores)
- [Langfuse Evaluation](https://langfuse.com/docs/scores/model-based-evals)
- [Langfuse Datasets](https://langfuse.com/docs/datasets)
