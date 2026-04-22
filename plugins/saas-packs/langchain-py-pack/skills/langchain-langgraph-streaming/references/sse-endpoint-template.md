# FastAPI SSE Endpoint Template for LangGraph Streaming

> Production-grade Server-Sent Events template with the anti-buffering headers your
> reverse proxy needs. Pin: `langgraph 1.0.x`, `fastapi >= 0.110`, `sse-starlette` optional.
> Pain-catalog anchors: P46 (proxy buffering), P48 (sync-invoke-in-async).

## The minimal correct endpoint

```python
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
# from your app:
from app.graph import build_graph

app = FastAPI()
graph = build_graph(checkpointer=MemorySaver())


def sse_pack(event: str, data: dict) -> str:
    """Format a single SSE event frame.

    SSE wire format: `event: <name>\ndata: <json>\n\n`
    The trailing blank line is the frame terminator — clients do not fire
    the event handler without it.
    """
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def stream_tokens(thread_id: str, user_input: str):
    """Yield SSE frames from a LangGraph run.

    Emits a heartbeat every 15s so proxies don't close idle connections,
    then per-token `token` events, then a final `done` event.
    """
    heartbeat_task = None
    queue: asyncio.Queue[str] = asyncio.Queue()

    async def heartbeat():
        while True:
            await asyncio.sleep(15)
            # SSE comment line — keeps connection open without firing a handler
            await queue.put(": heartbeat\n\n")

    async def producer():
        try:
            config = {"configurable": {"thread_id": thread_id}}
            async for chunk, metadata in graph.astream(
                {"messages": [HumanMessage(user_input)]},
                config=config,
                stream_mode="messages",
            ):
                # Only forward chunks with renderable text content.
                # chunk.content may be a list[dict] on Claude tool-use turns.
                text = chunk.text if hasattr(chunk, "text") else None
                if not text and isinstance(chunk.content, str):
                    text = chunk.content
                if text:
                    await queue.put(sse_pack("token", {
                        "text": text,
                        "node": metadata.get("langgraph_node"),
                    }))
            await queue.put(sse_pack("done", {"thread_id": thread_id}))
        except Exception as e:
            await queue.put(sse_pack("error", {"message": str(e)}))
        finally:
            await queue.put(None)  # sentinel

    heartbeat_task = asyncio.create_task(heartbeat())
    producer_task = asyncio.create_task(producer())

    try:
        while True:
            frame = await queue.get()
            if frame is None:
                break
            yield frame
    finally:
        heartbeat_task.cancel()
        producer_task.cancel()


@app.get("/stream")
async def stream(thread_id: str, q: str):
    """SSE endpoint. Required headers defeat proxy buffering (P46).

    Clients must use EventSource (browser) or an SSE library — plain
    fetch() without streaming support won't deliver events incrementally.
    """
    return StreamingResponse(
        stream_tokens(thread_id, q),
        media_type="text/event-stream",
        headers={
            # CRITICAL — Nginx / Cloud Run / Cloudflare buffer by default.
            # This header disables proxy buffering for the response.
            "X-Accel-Buffering": "no",
            # Prevent any cache layer from holding the stream.
            "Cache-Control": "no-cache",
            # Keep the TCP connection open for the full stream.
            "Connection": "keep-alive",
        },
    )
```

## The required headers — what each one does

| Header | Purpose | Skip it and… |
|--------|---------|--------------|
| `Content-Type: text/event-stream` | Tells clients and proxies this is SSE | Browsers won't fire `EventSource` handlers |
| `X-Accel-Buffering: no` | Nginx-recognized directive to disable response buffering | Nginx buffers 4-8KB before flushing — tokens arrive in bursts or not at all |
| `Cache-Control: no-cache` | Prevents intermediate caches from storing the stream | CDN or browser cache may serve a stale partial response |
| `Connection: keep-alive` | Keeps TCP connection open | Some proxies close the connection after the first event |

`StreamingResponse` in FastAPI sets `Transfer-Encoding: chunked` automatically. Do not set `Content-Length`.

## Heartbeat — why and when

Idle connections with no data for 30-60 seconds get closed by Cloud Run, some Nginx configurations, Cloudflare, and corporate proxies. During a long LLM call (e.g., a tool-using agent waiting on an API), no bytes flow. The SSE heartbeat (`: heartbeat\n\n` — a comment line that clients ignore) keeps the connection warm.

15 seconds is a safe default. Cloud Run's default idle timeout is 60 seconds; Cloudflare Free tier 100 seconds; Nginx `proxy_read_timeout` often 60 seconds. A 15-second heartbeat clears all of them with room.

## The client side

```javascript
const es = new EventSource(`/stream?thread_id=u-42&q=${encodeURIComponent(msg)}`);

es.addEventListener("token", (e) => {
  const { text, node } = JSON.parse(e.data);
  appendToChat(text);
});

es.addEventListener("done", (e) => {
  es.close();
});

es.addEventListener("error", (e) => {
  // EventSource auto-reconnects on network error by default.
  // Server errors arrive as named "error" events with JSON payload.
  const data = e.data ? JSON.parse(e.data) : null;
  showError(data?.message || "Stream failed");
  es.close();
});
```

`EventSource` reconnects automatically on transport errors. It does not resume mid-stream — your server should be idempotent on restart of a `thread_id` run (LangGraph checkpointers handle this if configured correctly; see `websocket-and-reconnect.md`).

## Reverse-proxy snippets

### Nginx

```nginx
location /stream {
    proxy_pass http://upstream;
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    # Disable buffering for SSE
    proxy_buffering off;
    proxy_cache off;

    # Extended timeouts for long streams
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    # Pass through any other SSE headers from upstream
    proxy_set_header X-Accel-Buffering no;

    # Required for chunked encoding to actually flush
    chunked_transfer_encoding on;
}
```

### Traefik (labels)

```yaml
labels:
  - "traefik.http.routers.api.rule=PathPrefix(`/stream`)"
  - "traefik.http.services.api.loadbalancer.sticky=true"
  - "traefik.http.services.api.loadbalancer.passhostheader=true"
  # Traefik 3.x honors upstream flush by default; extend read timeout if needed
  - "traefik.http.serversTransports.api.forwardingTimeouts.readIdleTimeout=300s"
```

### Cloud Run

```bash
# The service must be deployed with HTTP/2 end-to-end for streaming to flush
# chunks reliably. HTTP/1.1 works but is more prone to buffering intermediaries.
gcloud run deploy api \
  --image=IMAGE \
  --use-http2 \
  --timeout=3600 \
  --cpu-always-allocated \
  --min-instances=1
```

Cloud Run's HTTP/2 mode flushes chunks promptly; the `X-Accel-Buffering: no` header is redundant there but harmless. The 60-minute timeout is the request limit; set `--timeout` to cover your longest expected stream.

### Cloudflare

Cloudflare buffers by default on the Free plan. On paid plans, enable "Response Buffering: Off" in the page rules for the streaming path. If you can't disable buffering, your only option is to downgrade to long-polling or use WebSockets (which Cloudflare does not buffer).

## Testing the proxy path — not just localhost

This is non-negotiable. A stream that works from `uvicorn main:app` on your laptop will hang behind Cloud Run. Deploy to a throwaway service with the full proxy chain and verify:

```bash
# From a VM or laptop, hit the deployed endpoint. The tokens should arrive
# incrementally — not in one big burst at the end.
curl -N "https://your-service.run.app/stream?thread_id=t1&q=hi"
```

`curl -N` disables curl's own buffering. Watch the output stream. If tokens arrive all-at-once at the end, your proxy is buffering — add `X-Accel-Buffering: no`, check Cloud Run HTTP/2, check Cloudflare settings.

## Alternative — `sse-starlette`

If you'd rather not hand-roll SSE framing, `sse-starlette` provides an `EventSourceResponse` class:

```python
from sse_starlette.sse import EventSourceResponse

@app.get("/stream")
async def stream(thread_id: str, q: str):
    async def event_generator():
        async for chunk, metadata in graph.astream(
            {"messages": [HumanMessage(q)]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            text = chunk.text if hasattr(chunk, "text") else None
            if text:
                yield {"event": "token", "data": json.dumps({"text": text})}
        yield {"event": "done", "data": json.dumps({"thread_id": thread_id})}

    return EventSourceResponse(
        event_generator(),
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
```

`EventSourceResponse` handles heartbeat pings automatically via its `ping` parameter (default: every 15s).

## Sources

- [LangGraph streaming how-to](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Nginx `proxy_buffering` directive](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)
- [Cloud Run HTTP/2 end-to-end](https://cloud.google.com/run/docs/configuring/http2)
- Pack pain catalog: `docs/pain-catalog.md` entries P46, P48
