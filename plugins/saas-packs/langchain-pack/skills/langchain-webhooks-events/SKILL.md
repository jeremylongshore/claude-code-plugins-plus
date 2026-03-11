---
name: langchain-webhooks-events
description: |
  Implement LangChain callback and event handling for webhooks.
  Use when integrating with external systems, implementing streaming,
  or building event-driven LangChain applications.
  Trigger with phrases like "langchain callbacks", "langchain webhooks",
  "langchain events", "langchain streaming", "callback handler".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Webhooks & Events

## Overview
Implement callback handlers and event-driven patterns for LangChain applications including streaming, webhooks, and real-time updates.

## Prerequisites
- LangChain application configured
- Understanding of async programming
- Webhook endpoint (for external integrations)

## Instructions

### Step 1: Create Custom Callback Handler
```python
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from typing import Any, Dict, List
import httpx

class WebhookCallbackHandler(BaseCallbackHandler):
    """Send events to external webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.Client(timeout=10.0)

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs
    ) -> None:
        """Called when LLM starts."""
        self._send_event("llm_start", {
            "model": serialized.get("name"),
            "prompt_count": len(prompts)
        })

    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM completes."""
        self._send_event("llm_end", {
            "generations": len(response.generations),
            "token_usage": response.llm_output.get("token_usage") if response.llm_output else None
        })

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called on LLM error."""
        self._send_event("llm_error", {
            "error_type": type(error).__name__,
            "message": str(error)
        })

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs
    ) -> None:
        """Called when chain starts."""
        self._send_event("chain_start", {
            "chain": serialized.get("name"),
            "input_keys": list(inputs.keys())
        })

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain completes."""
        self._send_event("chain_end", {
            "output_keys": list(outputs.keys())
        })

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs
    ) -> None:
        """Called when tool starts."""
        self._send_event("tool_start", {
            "tool": serialized.get("name"),
            "input_length": len(input_str)
        })

    def _send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send event to webhook."""
        try:
            self.client.post(self.webhook_url, json={
                "event": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Webhook error: {e}")
```

### Step 2: Implement Streaming Handler
```python
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import asyncio
from typing import AsyncIterator

class StreamingWebSocketHandler(BaseCallbackHandler):
    """Stream tokens to WebSocket clients."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.queue = asyncio.Queue()

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called for each new token."""
        await self.queue.put(token)

    async def on_llm_end(self, response, **kwargs) -> None:
        """Signal end of stream."""
        await self.queue.put(None)

    async def stream_tokens(self) -> AsyncIterator[str]:
        """Iterate over streamed tokens."""
        while True:
            token = await self.queue.get()
            if token is None:
                break
            yield token

# FastAPI WebSocket endpoint
from fastapi import WebSocket

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    handler = StreamingWebSocketHandler(websocket)
    llm = ChatOpenAI(streaming=True, callbacks=[handler])

    while True:
        data = await websocket.receive_json()

        # Start streaming in background
        asyncio.create_task(chain.ainvoke(
            {"input": data["message"]},
            config={"callbacks": [handler]}
        ))

        # Stream tokens to client
        async for token in handler.stream_tokens():
            await websocket.send_json({"token": token})
```

### Step 3: Server-Sent Events (SSE)
```python
from fastapi import Request
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI

@app.get("/chat/stream")
async def stream_chat(request: Request, message: str):
    """Stream response using Server-Sent Events."""

    async def event_generator():
        llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
        prompt = ChatPromptTemplate.from_template("{input}")
        chain = prompt | llm

        async for chunk in chain.astream({"input": message}):
            if await request.is_disconnected():
                break
            yield f"data: {chunk.content}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Step 4: Event Aggregation
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class ChainEvent:
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

@dataclass
class ChainTrace:
    chain_id: str
    events: List[ChainEvent] = field(default_factory=list)
    start_time: datetime = None
    end_time: datetime = None

class TraceAggregator(BaseCallbackHandler):
    """Aggregate all events for a chain execution."""

    def __init__(self):
        self.traces: Dict[str, ChainTrace] = {}

    def on_chain_start(self, serialized, inputs, run_id, **kwargs):
        self.traces[str(run_id)] = ChainTrace(
            chain_id=str(run_id),
            start_time=datetime.now()
        )
        self._add_event(run_id, "chain_start", {"inputs": inputs})

    def on_chain_end(self, outputs, run_id, **kwargs):
        self._add_event(run_id, "chain_end", {"outputs": outputs})
        if str(run_id) in self.traces:
            self.traces[str(run_id)].end_time = datetime.now()

    def _add_event(self, run_id, event_type, data):
        trace = self.traces.get(str(run_id))
        if trace:
            trace.events.append(ChainEvent(
                event_type=event_type,
                timestamp=datetime.now(),
                data=data
            ))

    def get_trace(self, run_id: str) -> ChainTrace:
        return self.traces.get(run_id)
```

## Output
- Custom webhook callback handler
- WebSocket streaming implementation
- Server-Sent Events endpoint
- Event aggregation for tracing

## Examples

### Using Callbacks
```python
from langchain_openai import ChatOpenAI

webhook_handler = WebhookCallbackHandler("https://api.example.com/webhook")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    callbacks=[webhook_handler]
)

# All LLM calls will trigger webhook events
response = llm.invoke("Hello!")
```

### Client-Side SSE Consumption
```javascript
// JavaScript client
const eventSource = new EventSource('/chat/stream?message=Hello');

eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
        eventSource.close();
        return;
    }
    document.getElementById('output').textContent += event.data;
};
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webhook Timeout | Slow endpoint | Increase timeout, use async |
| WebSocket Disconnect | Client closed | Handle disconnect gracefully |
| Event Queue Full | Too many events | Add queue size limit |
| SSE Timeout | Long response | Add keep-alive pings |

## Resources
- [LangChain Callbacks](https://python.langchain.com/docs/concepts/callbacks/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## Next Steps
Use `langchain-observability` for comprehensive monitoring.