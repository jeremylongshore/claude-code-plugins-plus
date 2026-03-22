---
name: langchain-webhooks-events
description: |
  Implement LangChain callback handlers, streaming, webhooks,
  Server-Sent Events (SSE), and WebSocket integration.
  Trigger: "langchain callbacks", "langchain webhooks",
  "langchain events", "langchain streaming", "langchain SSE", "WebSocket LLM".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, webhooks]

---
# LangChain Webhooks & Events

## Overview

Event-driven patterns for LangChain: custom callback handlers for lifecycle hooks, webhook dispatching, Server-Sent Events (SSE) for streaming, WebSocket integration, and event aggregation for tracing.

## Callback Handler Architecture

LangChain emits events at every stage of chain/agent execution. Custom handlers can observe, log, stream, or dispatch these events.

```
chain.invoke()
  ├── handleChainStart()
  │   ├── handleLLMStart()
  │   │   ├── handleLLMNewToken()  // streaming
  │   │   └── handleLLMEnd()
  │   ├── handleToolStart()
  │   │   └── handleToolEnd()
  │   └── handleRetrieverStart()
  │       └── handleRetrieverEnd()
  └── handleChainEnd()
```

## Custom Callback Handler

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

class WebhookHandler extends BaseCallbackHandler {
  name = "WebhookHandler";

  constructor(private webhookUrl: string) {
    super();
  }

  async handleLLMStart(llm: any, prompts: string[]) {
    await this.send("llm_start", {
      model: llm?.id?.[2],
      promptCount: prompts.length,
    });
  }

  async handleLLMEnd(output: any) {
    await this.send("llm_end", {
      tokenUsage: output.llmOutput?.tokenUsage,
    });
  }

  async handleLLMError(error: Error) {
    await this.send("llm_error", {
      error: error.message,
    });
  }

  async handleToolStart(_tool: any, input: string) {
    await this.send("tool_start", { input: input.slice(0, 200) });
  }

  async handleToolEnd(output: string) {
    await this.send("tool_end", { output: output.slice(0, 200) });
  }

  private async send(event: string, data: Record<string, any>) {
    try {
      await fetch(this.webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event,
          data,
          timestamp: new Date().toISOString(),
        }),
        signal: AbortSignal.timeout(5000),
      });
    } catch (e) {
      // Don't let webhook failures break the chain
      console.warn(`Webhook error: ${e}`);
    }
  }
}

// Attach to model
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  callbacks: [new WebhookHandler("https://api.example.com/webhook")],
});
```

## Server-Sent Events (SSE) Endpoint

```typescript
import express from "express";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const app = express();
app.use(express.json());

const chain = ChatPromptTemplate.fromTemplate("{input}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", streaming: true }))
  .pipe(new StringOutputParser());

app.post("/api/chat/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  try {
    const stream = await chain.stream({ input: req.body.input });

    for await (const chunk of stream) {
      if (res.destroyed) break;  // client disconnected
      res.write(`data: ${JSON.stringify({ text: chunk })}\n\n`);
    }

    res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
  } catch (error: any) {
    res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
  }

  res.end();
});
```

### Client-Side SSE Consumer

```typescript
// Browser JavaScript
async function streamChat(input: string) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split("\n").filter((l) => l.startsWith("data: "));

    for (const line of lines) {
      const data = JSON.parse(line.slice(6));
      if (data.done) return;
      if (data.text) document.getElementById("output")!.textContent += data.text;
    }
  }
}
```

## WebSocket Streaming

```typescript
import { WebSocketServer } from "ws";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const wss = new WebSocketServer({ port: 8080 });

const chain = ChatPromptTemplate.fromTemplate("{input}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini", streaming: true }))
  .pipe(new StringOutputParser());

wss.on("connection", (ws) => {
  ws.on("message", async (raw) => {
    const { input } = JSON.parse(raw.toString());

    try {
      const stream = await chain.stream({ input });
      for await (const chunk of stream) {
        if (ws.readyState !== ws.OPEN) break;
        ws.send(JSON.stringify({ type: "token", text: chunk }));
      }
      ws.send(JSON.stringify({ type: "done" }));
    } catch (error: any) {
      ws.send(JSON.stringify({ type: "error", message: error.message }));
    }
  });
});
```

## Event Aggregation (Trace Collection)

```typescript
interface TraceEvent {
  event: string;
  timestamp: number;
  data: Record<string, any>;
  runId: string;
}

class TraceAggregator extends BaseCallbackHandler {
  name = "TraceAggregator";
  events: TraceEvent[] = [];

  handleChainStart(_chain: any, inputs: any, runId: string) {
    this.log("chain_start", runId, { inputKeys: Object.keys(inputs) });
  }

  handleChainEnd(outputs: any, runId: string) {
    this.log("chain_end", runId, { outputKeys: Object.keys(outputs) });
  }

  handleLLMStart(llm: any, _prompts: string[], runId: string) {
    this.log("llm_start", runId, { model: llm?.id?.[2] });
  }

  handleLLMEnd(output: any, runId: string) {
    this.log("llm_end", runId, {
      tokens: output.llmOutput?.tokenUsage?.totalTokens,
    });
  }

  private log(event: string, runId: string, data: Record<string, any>) {
    this.events.push({ event, timestamp: Date.now(), data, runId });
  }

  getTrace() {
    return {
      events: this.events,
      totalEvents: this.events.length,
      durationMs: this.events.length > 1
        ? this.events[this.events.length - 1].timestamp - this.events[0].timestamp
        : 0,
    };
  }
}

// Usage
const tracer = new TraceAggregator();
await chain.invoke({ input: "test" }, { callbacks: [tracer] });
console.log(tracer.getTrace());
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Webhook timeout | Slow endpoint | Use `AbortSignal.timeout()`, make async |
| WebSocket disconnect | Client closed | Check `ws.readyState` before sending |
| SSE connection reset | Proxy timeout | Add keep-alive pings every 15s |
| Events not captured | Callback not passed | Add to `callbacks` array in `invoke()` |

## Resources

- [LangChain Callbacks](https://js.langchain.com/docs/concepts/callbacks/)
- [LangChain Streaming](https://js.langchain.com/docs/how_to/streaming/)
- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [ws Package](https://www.npmjs.com/package/ws)

## Next Steps

Use `langchain-observability` for comprehensive production monitoring.
