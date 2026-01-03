# openrouter-streaming-setup

> Configure streaming responses for real-time applications

## Directory Structure

```
openrouter-streaming-setup/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 stream_handler.py       # Streaming response handler
    ├── 🐍 websocket_stream.py     # WebSocket streaming
    └── 🐍 sse_endpoint.py         # Server-Sent Events endpoint
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with streaming configuration guide |
| `stream_handler.py` | 🐍 Python | Handle streaming responses |
| `websocket_stream.py` | 🐍 Python | WebSocket-based streaming |
| `sse_endpoint.py` | 🐍 Python | SSE endpoint implementation |

## Summary

**Category:** cicd
**Target Audience:** Developer building real-time apps
**Trigger Phrases:** `openrouter streaming`, `openrouter stream`, `openrouter real-time`, `openrouter sse`

### What This Skill Does

This skill teaches configuring streaming responses for real-time applications. It covers:

- OpenAI SDK streaming configuration
- Token-by-token processing
- Server-Sent Events (SSE) endpoints
- WebSocket streaming patterns
- Stream interruption handling
- Progress indicators

### Technical Success Criteria

- Smooth streaming with proper token handling
- SSE or WebSocket endpoint working
- Error handling during streams

### Business Success Criteria

- Responsive user experience
- Real-time feedback to users
- Perceived faster response times

## Related Skills

- `openrouter-sdk-patterns` - SDK streaming configuration
- `openrouter-hello-world` - Basic request patterns
- `openrouter-performance-tuning` - Stream optimization
