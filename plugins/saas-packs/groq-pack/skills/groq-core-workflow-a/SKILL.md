---
name: groq-core-workflow-a
description: |
  Execute Groq primary workflow: chat completions with tool use and JSON mode.
  Use when implementing chat interfaces, function calling, structured output,
  or building AI features with Groq's fast inference.
  Trigger with phrases like "groq chat completion", "groq tool use",
  "groq function calling", "groq JSON mode".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, workflow]

---
# Groq Core Workflow A: Chat, Tools & Structured Output

## Overview
Primary integration patterns for Groq: chat completions, tool/function calling, JSON mode, and structured outputs. Groq's LPU delivers sub-200ms time-to-first-token, making these patterns viable for real-time user-facing features.

## Prerequisites
- `groq-sdk` installed, `GROQ_API_KEY` set
- Understanding of Groq model capabilities

## Model Selection for This Workflow

| Task | Recommended Model | Why |
|------|------------------|-----|
| Chat with tools | `llama-3.3-70b-versatile` | Best tool-calling accuracy |
| JSON extraction | `llama-3.1-8b-instant` | Fast, accurate for structured tasks |
| Structured outputs | `llama-3.3-70b-versatile` | Supports `strict: true` schema compliance |
| Vision + chat | `meta-llama/llama-4-scout-17b-16e-instruct` | Multimodal input |

## Instructions

### Step 1: Chat Completion with System Prompt
```typescript
import Groq from "groq-sdk";

const groq = new Groq();

async function chat(userMessage: string, history: any[] = []) {
  const messages = [
    { role: "system" as const, content: "You are a concise technical assistant." },
    ...history,
    { role: "user" as const, content: userMessage },
  ];

  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages,
    temperature: 0.7,
    max_tokens: 1024,
  });

  return {
    reply: completion.choices[0].message.content,
    usage: completion.usage,
  };
}
```

### Step 2: Tool Use / Function Calling
```typescript
// Define tools with JSON Schema
const tools: Groq.Chat.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get current weather for a location",
      parameters: {
        type: "object",
        properties: {
          location: { type: "string", description: "City name" },
          unit: { type: "string", enum: ["celsius", "fahrenheit"] },
        },
        required: ["location"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "search_docs",
      description: "Search internal documentation",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string" },
          limit: { type: "number", description: "Max results" },
        },
        required: ["query"],
      },
    },
  },
];

async function chatWithTools(userMessage: string) {
  // Step A: Send message with tool definitions
  const response = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: userMessage }],
    tools,
    tool_choice: "auto",
  });

  const message = response.choices[0].message;

  // Step B: If model wants to call tools, execute them
  if (message.tool_calls) {
    const toolResults = await Promise.all(
      message.tool_calls.map(async (tc) => {
        const args = JSON.parse(tc.function.arguments);
        const result = await executeFunction(tc.function.name, args);
        return {
          role: "tool" as const,
          tool_call_id: tc.id,
          content: JSON.stringify(result),
        };
      })
    );

    // Step C: Send tool results back for final response
    const finalResponse = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "user", content: userMessage },
        message,         // includes tool_calls
        ...toolResults,  // tool execution results
      ],
      tools,
    });

    return finalResponse.choices[0].message.content;
  }

  return message.content;
}

// Implement your actual tool functions
async function executeFunction(name: string, args: any): Promise<any> {
  switch (name) {
    case "get_weather":
      return { temperature: 72, conditions: "sunny", location: args.location };
    case "search_docs":
      return { results: [`Doc about ${args.query}`], count: 1 };
    default:
      throw new Error(`Unknown function: ${name}`);
  }
}
```

### Step 3: JSON Mode
```typescript
// Force model to return valid JSON
async function extractJSON(text: string) {
  const completion = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      {
        role: "system",
        content: "Extract entities from the text. Respond with JSON: {entities: [{name, type, confidence}]}",
      },
      { role: "user", content: text },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
  });

  return JSON.parse(completion.choices[0].message.content!);
}
```

### Step 4: Structured Outputs (Strict Schema)
```typescript
// Guaranteed schema compliance -- no validation needed
async function extractStructured(text: string) {
  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "system", content: "Extract contact information from the text." },
      { role: "user", content: text },
    ],
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "contact_info",
        strict: true,
        schema: {
          type: "object",
          properties: {
            name: { type: "string" },
            email: { type: "string" },
            phone: { type: "string" },
            company: { type: "string" },
          },
          required: ["name", "email"],
          additionalProperties: false,
        },
      },
    },
  });

  // With strict: true, output is guaranteed to match schema
  return JSON.parse(completion.choices[0].message.content!);
}
```

**Limitation**: Streaming and tool use are not supported with Structured Outputs. Use non-streaming mode when using `response_format` with `json_schema`.

### Step 5: Multi-Turn Conversation
```typescript
class GroqConversation {
  private messages: Groq.Chat.ChatCompletionMessageParam[] = [];

  constructor(private systemPrompt: string) {
    this.messages.push({ role: "system", content: systemPrompt });
  }

  async send(userMessage: string): Promise<string> {
    this.messages.push({ role: "user", content: userMessage });

    const completion = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: this.messages,
      max_tokens: 1024,
    });

    const reply = completion.choices[0].message;
    this.messages.push(reply);
    return reply.content || "";
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `tool_calls` with malformed JSON | Model hallucinated arguments | Wrap `JSON.parse` in try/catch, retry with lower temperature |
| `json_object` returns non-JSON | System prompt missing JSON instruction | Always include "respond with JSON" in system prompt |
| `context_length_exceeded` | Conversation too long | Trim older messages, keep system prompt |
| Tool call loop | Model keeps calling tools | Set `tool_choice: "none"` on final completion |

## Resources
- [Groq Tool Use Docs](https://console.groq.com/docs/tool-use)
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs)
- [Groq Text Generation](https://console.groq.com/docs/text-chat)

## Next Steps
For audio, vision, and speech workflows, see `groq-core-workflow-b`.
