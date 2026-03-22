---
name: cohere-core-workflow-b
description: |
  Build tool-use agents and function calling with Cohere API v2.
  Use when implementing multi-step agents, function calling,
  or building autonomous tool-using workflows with Cohere.
  Trigger with phrases like "cohere tool use", "cohere agents",
  "cohere function calling", "cohere multi-step".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Tool Use & Agents (Core Workflow B)

## Overview
Build multi-step tool-using agents with Cohere's Chat API v2. The model decides which tools to call, you execute them, and feed results back in a loop until the task is complete.

## Prerequisites
- Completed `cohere-install-auth` setup
- Understanding of `cohere-core-workflow-a` (RAG)
- Command R7B or newer model (required for tool use)

## Instructions

### Step 1: Define Tools

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

// Define tools the model can call
const tools = [
  {
    type: 'function' as const,
    function: {
      name: 'get_weather',
      description: 'Get current weather for a city',
      parameters: {
        type: 'object' as const,
        properties: {
          city: { type: 'string', description: 'City name' },
          unit: { type: 'string', enum: ['celsius', 'fahrenheit'], description: 'Temperature unit' },
        },
        required: ['city'],
      },
    },
  },
  {
    type: 'function' as const,
    function: {
      name: 'search_database',
      description: 'Search internal database for records',
      parameters: {
        type: 'object' as const,
        properties: {
          query: { type: 'string', description: 'Search query' },
          limit: { type: 'number', description: 'Max results' },
        },
        required: ['query'],
      },
    },
  },
];
```

### Step 2: Implement Tool Executors

```typescript
// Map tool names to actual implementations
const toolExecutors: Record<string, (args: any) => Promise<string>> = {
  get_weather: async ({ city, unit = 'celsius' }) => {
    // Replace with real weather API call
    return JSON.stringify({
      city,
      temperature: unit === 'celsius' ? 22 : 72,
      unit,
      condition: 'partly cloudy',
    });
  },

  search_database: async ({ query, limit = 5 }) => {
    // Replace with real database query
    return JSON.stringify({
      results: [
        { id: 1, title: `Result for: ${query}`, relevance: 0.95 },
      ],
      total: 1,
    });
  },
};
```

### Step 3: Single-Step Tool Use

```typescript
async function singleStepToolUse(userMessage: string) {
  // 1. Send message with tools
  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: userMessage }],
    tools,
  });

  // 2. Check if model wants to call tools
  if (response.finishReason === 'TOOL_CALL') {
    const toolCalls = response.message?.toolCalls ?? [];

    // 3. Execute each tool call
    const toolResults = await Promise.all(
      toolCalls.map(async (tc) => {
        const executor = toolExecutors[tc.function.name];
        const args = JSON.parse(tc.function.arguments);
        const result = await executor(args);
        return {
          call: tc,
          outputs: [{ result }],
        };
      })
    );

    // 4. Send tool results back for final answer
    const finalResponse = await cohere.chat({
      model: 'command-a-03-2025',
      messages: [
        { role: 'user', content: userMessage },
        { role: 'assistant', toolCalls },
        { role: 'tool', toolCallId: toolCalls[0].id, content: toolResults[0].outputs[0].result },
      ],
      tools,
    });

    return finalResponse.message?.content?.[0]?.text ?? '';
  }

  // No tool call — direct response
  return response.message?.content?.[0]?.text ?? '';
}
```

### Step 4: Multi-Step Agent Loop

```typescript
async function agentLoop(userMessage: string, maxSteps = 5) {
  const messages: any[] = [{ role: 'user', content: userMessage }];

  for (let step = 0; step < maxSteps; step++) {
    const response = await cohere.chat({
      model: 'command-a-03-2025',
      messages,
      tools,
    });

    // If model is done (no tool calls), return the answer
    if (response.finishReason !== 'TOOL_CALL') {
      return response.message?.content?.[0]?.text ?? '';
    }

    // Model wants to call tools
    const toolCalls = response.message?.toolCalls ?? [];
    messages.push({ role: 'assistant', toolCalls });

    // Execute tools (parallel if multiple)
    for (const tc of toolCalls) {
      const executor = toolExecutors[tc.function.name];
      if (!executor) {
        messages.push({ role: 'tool', toolCallId: tc.id, content: `Error: Unknown tool ${tc.function.name}` });
        continue;
      }

      try {
        const args = JSON.parse(tc.function.arguments);
        const result = await executor(args);
        messages.push({ role: 'tool', toolCallId: tc.id, content: result });
      } catch (err) {
        messages.push({ role: 'tool', toolCallId: tc.id, content: `Error: ${(err as Error).message}` });
      }
    }

    console.log(`Step ${step + 1}: executed ${toolCalls.length} tool(s)`);
  }

  return 'Agent reached max steps without completing.';
}

// Usage
const answer = await agentLoop("What's the weather in Tokyo and search for 'Tokyo events'?");
console.log(answer);
```

### Step 5: Force Tool Use

```typescript
// Force the model to use at least one tool
const response = await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: 'Look up the weather in Paris' }],
  tools,
  toolChoice: 'REQUIRED', // REQUIRED = must use tool, NONE = cannot use tools
});

// toolChoice options:
// - omitted: model decides freely
// - 'REQUIRED': must call at least one tool
// - 'NONE': cannot call any tools (text-only response)
```

### Step 6: Streaming Tool Use

```typescript
async function streamWithTools(userMessage: string) {
  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: userMessage }],
    tools,
  });

  const toolCalls: any[] = [];

  for await (const event of stream) {
    switch (event.type) {
      case 'tool-call-start':
        console.log(`Tool call: ${event.delta?.message?.toolCalls?.function?.name}`);
        break;
      case 'tool-call-delta':
        // Streaming tool arguments
        break;
      case 'content-delta':
        process.stdout.write(event.delta?.message?.content?.text ?? '');
        break;
    }
  }
}
```

## Output
- Single-step tool calls with automatic execution
- Multi-step agent loop handling sequential reasoning
- Parallel tool execution for independent calls
- Streaming with tool-call events

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `tool not found` | Mismatched tool name | Verify `tools` array matches executors |
| `invalid arguments` | Schema mismatch | Check tool parameter types |
| Infinite loop | Model keeps calling tools | Set `maxSteps` limit |
| `TOOL_CALL` with no toolCalls | Edge case | Check `response.message?.toolCalls` length |

## Resources
- [Tool Use Quickstart](https://docs.cohere.com/docs/tool-use-quickstart)
- [Multi-Step Tool Use](https://docs.cohere.com/docs/multi-step-tool-use)
- [Tool Use Streaming](https://docs.cohere.com/docs/tool-use-streaming)
- [Tool Use Citations](https://docs.cohere.com/docs/tool-use-citations)

## Next Steps
For common errors, see `cohere-common-errors`.
