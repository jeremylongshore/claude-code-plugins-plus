---
name: anthropic-architecture-variants
description: |
  Build different types of Claude-powered applications — chatbots, RAG systems,
  agents, content pipelines, and code generation tools.
  Trigger with "claude architecture", "anthropic rag", "build with claude",
  "claude agent pattern", "anthropic app design".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, architecture, rag, agents]
---

# Claude Architecture Variants

## Overview
Core functionality and patterns for anthropic-architecture-variants.


## 1. Chatbot (Stateless API Wrapper)
Simplest pattern — proxy Claude with a system prompt.
```typescript
// api/chat.ts
export async function POST(req: Request) {
  const { messages } = await req.json();
  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    system: 'You are a helpful assistant for our SaaS product.',
    messages,
    stream: true,
  });
  return new Response(response.toReadableStream());
}
```
**Best for:** Customer support, Q&A, simple conversational interfaces.

## 2. RAG (Retrieval-Augmented Generation)
Fetch relevant context, inject into prompt, generate grounded answer.
```typescript
async function ragQuery(question: string) {
  // 1. Embed the question (use Voyage, OpenAI, or Cohere — not Anthropic)
  const embedding = await embeddingClient.embed(question);

  // 2. Search vector DB for relevant chunks
  const chunks = await vectorDb.query(embedding, { topK: 5 });

  // 3. Send to Claude with context
  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2048,
    system: `Answer based on the provided context. If the context doesn't contain the answer, say so.`,
    messages: [{
      role: 'user',
      content: `Context:\n${chunks.map(c => c.text).join('\n---\n')}\n\nQuestion: ${question}`,
    }],
  });
  return message.content[0].text;
}
```
**Best for:** Documentation Q&A, knowledge bases, support with source citations.

## 3. Agent (Tool Use Loop)
Claude decides which tools to call, you execute them, loop until done.
```typescript
async function agentLoop(userInput: string, tools: Anthropic.Tool[]) {
  let messages: MessageParam[] = [{ role: 'user', content: userInput }];

  while (true) {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      tools,
      messages,
    });
    messages.push({ role: 'assistant', content: response.content });

    if (response.stop_reason === 'end_turn') {
      return response.content.find(b => b.type === 'text')?.text;
    }

    // Execute tools
    const results = [];
    for (const block of response.content) {
      if (block.type === 'tool_use') {
        const result = await executeTool(block.name, block.input);
        results.push({ type: 'tool_result', tool_use_id: block.id, content: JSON.stringify(result) });
      }
    }
    messages.push({ role: 'user', content: results });
  }
}
```
**Best for:** Data analysis, code generation, multi-step workflows.

## 4. Content Pipeline (Batch Processing)
Process thousands of documents through Claude asynchronously.
```typescript
const batch = await client.messages.batches.create({
  requests: documents.map((doc, i) => ({
    custom_id: doc.id,
    params: {
      model: 'claude-haiku-4-5-20251001', // Cheap for bulk
      max_tokens: 512,
      messages: [{ role: 'user', content: `Extract entities: ${doc.text}` }],
    },
  })),
});
// 50% cheaper, processes within 24h
```
**Best for:** Summarization, classification, extraction at scale.

## 5. Evaluation / Grading
Use Claude to evaluate other AI outputs or human content.
```typescript
const evaluation = await client.messages.create({
  model: 'claude-opus-4-20250514', // Best judgment
  max_tokens: 1024,
  system: `You are an expert evaluator. Score the response 1-5 on accuracy, relevance, and completeness. Return JSON: { "accuracy": N, "relevance": N, "completeness": N, "reasoning": "..." }`,
  messages: [{
    role: 'user',
    content: `Question: ${question}\nResponse to evaluate: ${candidateResponse}`,
  }],
});
```
**Best for:** AI output quality, content moderation, automated grading.

## Choosing a Pattern
| Pattern | Latency | Cost | Complexity |
|---------|---------|------|------------|
| Chatbot | Low (streaming) | Low | Simple |
| RAG | Medium (embed + search + generate) | Medium | Medium |
| Agent | High (multi-turn) | High | Complex |
| Pipeline | High (async batch) | Low (50% off) | Simple |
| Evaluation | Medium | Varies | Simple |

## Output
- Successful operation confirmed
- Results logged to console

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| API Error | Check error type and status code | See `anthropic-common-errors` |

## Examples
See code blocks above for complete examples.

## Resources
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)

## Next Steps
See `anthropic-known-pitfalls` for common mistakes.

## Prerequisites
- Completed `anthropic-architecture-install-auth` setup
- Valid API credentials configured

## Instructions
Follow the steps in the sections above.
