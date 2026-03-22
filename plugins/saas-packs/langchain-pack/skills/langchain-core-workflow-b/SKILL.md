---
name: langchain-core-workflow-b
description: |
  Build LangChain agents with tool calling for autonomous task execution.
  Use when creating AI agents, implementing tool/function calling,
  binding tools to models, or building autonomous multi-step workflows.
  Trigger: "langchain agents", "langchain tools", "tool calling",
  "create agent", "function calling", "createToolCallingAgent".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, workflow]

---
# LangChain Core Workflow B: Agents & Tools

## Overview

Build autonomous agents that use tools, make decisions, and execute multi-step tasks. Covers tool definition with Zod schemas, `createToolCallingAgent`, `AgentExecutor`, streaming agent output, and conversation memory.

## Prerequisites

- Completed `langchain-core-workflow-a` (chains)
- `npm install langchain @langchain/core @langchain/openai zod`

## Step 1: Define Tools (TypeScript)

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";

// Tool with Zod schema validation
const calculator = tool(
  async ({ expression }) => {
    try {
      // Use a safe math parser in production (e.g., mathjs)
      const result = Function(`"use strict"; return (${expression})`)();
      return String(result);
    } catch (e) {
      return `Error: invalid expression "${expression}"`;
    }
  },
  {
    name: "calculator",
    description: "Evaluate a mathematical expression. Input: a math expression string.",
    schema: z.object({
      expression: z.string().describe("Math expression like '2 + 2' or '100 * 0.15'"),
    }),
  }
);

const weatherLookup = tool(
  async ({ city }) => {
    // Replace with real API call
    const data: Record<string, string> = {
      "New York": "72F, sunny",
      "London": "58F, cloudy",
      "Tokyo": "80F, humid",
    };
    return data[city] ?? `No weather data for ${city}`;
  },
  {
    name: "weather",
    description: "Get current weather for a city.",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  }
);

const tools = [calculator, weatherLookup];
```

## Step 2: Create Agent with AgentExecutor

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { createToolCallingAgent, AgentExecutor } from "langchain/agents";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

const llm = new ChatOpenAI({ model: "gpt-4o-mini" });

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant. Use tools when needed."],
  new MessagesPlaceholder("chat_history"),
  ["human", "{input}"],
  new MessagesPlaceholder("agent_scratchpad"),
]);

const agent = createToolCallingAgent({
  llm,
  tools,
  prompt,
});

const executor = new AgentExecutor({
  agent,
  tools,
  verbose: true,           // Log reasoning steps
  maxIterations: 10,       // Prevent infinite loops
  returnIntermediateSteps: true,
});
```

## Step 3: Run the Agent

```typescript
// Simple invocation
const result = await executor.invoke({
  input: "What's 25 * 4, and what's the weather in Tokyo?",
  chat_history: [],
});

console.log(result.output);
// "25 * 4 = 100. The weather in Tokyo is 80F and humid."

// The agent decided to call both tools, then composed the answer.
console.log(result.intermediateSteps);
// Shows each tool call and its result
```

## Step 4: Agent with Conversation Memory

```typescript
import { ChatMessageHistory } from "@langchain/community/stores/message/in_memory";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";

const messageHistory = new ChatMessageHistory();

const agentWithHistory = new RunnableWithMessageHistory({
  runnable: executor,
  getMessageHistory: (_sessionId) => messageHistory,
  inputMessagesKey: "input",
  historyMessagesKey: "chat_history",
});

// First call
await agentWithHistory.invoke(
  { input: "My name is Alice" },
  { configurable: { sessionId: "user-1" } }
);

// Second call -- agent remembers
const res = await agentWithHistory.invoke(
  { input: "What's my name?" },
  { configurable: { sessionId: "user-1" } }
);
console.log(res.output); // "Your name is Alice!"
```

## Step 5: Stream Agent Events

```typescript
const eventStream = executor.streamEvents(
  { input: "Calculate 15% tip on $85", chat_history: [] },
  { version: "v2" }
);

for await (const event of eventStream) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data.chunk.content ?? "");
  } else if (event.event === "on_tool_start") {
    console.log(`\n[Calling tool: ${event.name}]`);
  } else if (event.event === "on_tool_end") {
    console.log(`[Tool result: ${event.data.output}]`);
  }
}
```

## Step 6: Bind Tools Directly (Without AgentExecutor)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage } from "@langchain/core/messages";

const model = new ChatOpenAI({ model: "gpt-4o-mini" });
const modelWithTools = model.bindTools(tools);

const response = await modelWithTools.invoke([
  new HumanMessage("What's 42 * 17?"),
]);

// Check if model wants to call a tool
if (response.tool_calls && response.tool_calls.length > 0) {
  for (const tc of response.tool_calls) {
    console.log(`Tool: ${tc.name}, Args: ${JSON.stringify(tc.args)}`);
    // Execute tool manually
    const toolResult = await tools
      .find((t) => t.name === tc.name)!
      .invoke(tc.args);
    console.log(`Result: ${toolResult}`);
  }
}
```

## Python Equivalent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

tools = [calculator]
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.invoke({"input": "What is 25 * 4?", "chat_history": []})
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Max iterations reached` | Agent stuck in loop | Increase `maxIterations` or improve system prompt |
| `Tool not found` | Tool name mismatch | Verify tools array passed to both `createToolCallingAgent` and `AgentExecutor` |
| `Missing agent_scratchpad` | Prompt missing placeholder | Add `new MessagesPlaceholder("agent_scratchpad")` |
| Tool execution error | Tool throws exception | Wrap tool body in try/catch, return error string |

## Resources

- [Agents Guide](https://js.langchain.com/docs/concepts/agents/)
- [Tool Calling](https://js.langchain.com/docs/concepts/tool_calling/)
- [createToolCallingAgent API](https://v03.api.js.langchain.com/functions/langchain.agents.createToolCallingAgent.html)

## Next Steps

Proceed to `langchain-common-errors` for debugging guidance.
