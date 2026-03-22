---
name: langfuse-core-workflow-b
description: |
  Execute Langfuse secondary workflow: Evaluation, scoring, and datasets.
  Use when implementing LLM evaluation, adding user feedback,
  or setting up automated quality scoring and experiment datasets.
  Trigger with phrases like "langfuse evaluation", "langfuse scoring",
  "rate llm outputs", "langfuse feedback", "langfuse datasets", "langfuse experiments".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, llm, workflow, evaluation]

---
# Langfuse Core Workflow B: Evaluation, Scoring & Datasets

## Overview
Implement LLM output evaluation using Langfuse scores (numeric, categorical, boolean), the experiment runner SDK for dataset-driven benchmarks, prompt management with versioned prompts, and LLM-as-a-Judge evaluation patterns.

## Prerequisites
- Langfuse SDK configured with API keys
- Traces already being collected (see `langfuse-core-workflow-a`)
- For v4+: `@langfuse/client` installed

## Instructions

### Step 1: Score Traces via SDK

Langfuse supports three score data types: **Numeric**, **Categorical**, and **Boolean**.

```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Numeric score (e.g., 0-1 quality rating)
await langfuse.score.create({
  traceId: "trace-abc-123",
  name: "relevance",
  value: 0.92,
  dataType: "NUMERIC",
  comment: "Highly relevant answer with good context usage",
});

// Categorical score (e.g., pass/fail classification)
await langfuse.score.create({
  traceId: "trace-abc-123",
  observationId: "gen-xyz-456", // Optional: score a specific generation
  name: "quality-tier",
  value: "excellent",
  dataType: "CATEGORICAL",
});

// Boolean score (e.g., thumbs up/down)
await langfuse.score.create({
  traceId: "trace-abc-123",
  name: "user-approved",
  value: 1, // 1 = true, 0 = false
  dataType: "BOOLEAN",
  comment: "User clicked thumbs up",
});
```

### Step 2: User Feedback Collection

```typescript
// API endpoint for frontend feedback widget
app.post("/api/feedback", async (req, res) => {
  const { traceId, rating, comment } = req.body;

  // Thumbs up/down
  await langfuse.score.create({
    traceId,
    name: "user-feedback",
    value: rating === "positive" ? 1 : 0,
    dataType: "BOOLEAN",
    comment,
  });

  // Granular star rating (1-5)
  if (req.body.stars) {
    await langfuse.score.create({
      traceId,
      name: "star-rating",
      value: req.body.stars,
      dataType: "NUMERIC",
      comment: `${req.body.stars}/5 stars`,
    });
  }

  res.json({ success: true });
});
```

### Step 3: Prompt Management

```typescript
// Fetch a versioned prompt from Langfuse
const textPrompt = await langfuse.prompt.get("summarize-article", {
  type: "text",
  label: "production", // or "latest", "staging"
});

// Compile with variables -- replaces {{variable}} placeholders
const compiled = textPrompt.compile({
  maxLength: "100 words",
  tone: "professional",
});

// Chat prompts return message arrays
const chatPrompt = await langfuse.prompt.get("customer-support", {
  type: "chat",
});

const messages = chatPrompt.compile({
  customerName: "Alice",
  issue: "billing question",
});
// messages = [{ role: "system", content: "..." }, { role: "user", content: "..." }]
```

### Step 4: Create and Populate Datasets

```typescript
// Create a dataset for evaluation
await langfuse.api.datasets.create({
  name: "customer-support-v1",
  description: "Test cases for customer support chatbot",
  metadata: { version: "1.0", domain: "support" },
});

// Add test items
const testCases = [
  {
    input: { query: "How do I cancel my subscription?" },
    expectedOutput: { intent: "cancellation", sentiment: "neutral" },
    metadata: { category: "billing" },
  },
  {
    input: { query: "Your product is amazing!" },
    expectedOutput: { intent: "feedback", sentiment: "positive" },
    metadata: { category: "feedback" },
  },
];

for (const testCase of testCases) {
  await langfuse.api.datasetItems.create({
    datasetName: "customer-support-v1",
    input: testCase.input,
    expectedOutput: testCase.expectedOutput,
    metadata: testCase.metadata,
  });
}
```

### Step 5: Run Experiments with the Experiment Runner

```typescript
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

// Define the task function -- your LLM application logic
async function classifyIntent(input: { query: string }): Promise<string> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: "Classify the user intent. Return one word." },
      { role: "user", content: input.query },
    ],
    temperature: 0,
  });
  return response.choices[0].message.content?.trim() || "";
}

// Define evaluator functions
function exactMatch({ output, expectedOutput }: {
  output: string;
  expectedOutput: { intent: string };
}) {
  return {
    name: "exact-match",
    value: output.toLowerCase() === expectedOutput.intent.toLowerCase() ? 1 : 0,
    dataType: "BOOLEAN" as const,
  };
}

// Run the experiment
const result = await langfuse.runExperiment({
  datasetName: "customer-support-v1",
  runName: "gpt-4o-mini-classifier-v1",
  runDescription: "Testing intent classification with gpt-4o-mini",
  task: classifyIntent,
  evaluators: [exactMatch],
});

console.log(`Experiment complete. ${result.runs.length} items evaluated.`);
// View results in Langfuse UI: Datasets > customer-support-v1 > Runs
```

### Step 6: LLM-as-a-Judge Evaluation

```typescript
async function llmJudge({ output, input, expectedOutput }: {
  output: string;
  input: { query: string };
  expectedOutput: { intent: string; sentiment: string };
}) {
  const judgment = await openai.chat.completions.create({
    model: "gpt-4o",
    temperature: 0,
    messages: [
      {
        role: "system",
        content: `You are an AI evaluator. Score the response 0-10 on accuracy and helpfulness.
Return JSON: {"score": <number>, "reasoning": "<explanation>"}`,
      },
      {
        role: "user",
        content: `Query: ${input.query}\nExpected: ${JSON.stringify(expectedOutput)}\nActual: ${output}`,
      },
    ],
    response_format: { type: "json_object" },
  });

  const result = JSON.parse(judgment.choices[0].message.content || "{}");

  return {
    name: "llm-judge-quality",
    value: result.score / 10, // Normalize to 0-1
    dataType: "NUMERIC" as const,
    comment: result.reasoning,
  };
}

// Use as an evaluator in experiments
await langfuse.runExperiment({
  datasetName: "customer-support-v1",
  runName: "judge-evaluation-v1",
  task: classifyIntent,
  evaluators: [exactMatch, llmJudge],
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Scores not appearing | API call failed silently | Await `score.create()` and check for errors |
| Score validation error | Wrong data type | Match `value` type to `dataType` (number/string/0-1) |
| LLM judge inconsistent | High temperature | Set `temperature: 0` for evaluation calls |
| Dataset item missing | Wrong dataset name | Verify exact name match (case-sensitive) |
| Experiment not in UI | Run not flushed | Check `runExperiment` completed without errors |

## Resources
- [Scores via API/SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
- [Datasets & Experiments](https://langfuse.com/docs/evaluation/experiments/datasets)
- [Experiment Runner SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Prompt Management](https://langfuse.com/docs/prompt-management/get-started)
- [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

## Next Steps
For common error debugging, see `langfuse-common-errors`. For CI/CD integration of evaluations, see `langfuse-ci-integration`.
