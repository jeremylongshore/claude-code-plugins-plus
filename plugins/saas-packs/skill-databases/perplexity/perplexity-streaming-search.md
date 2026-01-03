# perplexity-streaming-search

> Configure streaming responses for real-time search applications

## Directory Structure

```
perplexity-streaming-search/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── streaming_client.py     # Streaming search implementation
    ├── sse_handler.py          # Server-Sent Events handler
    ├── streaming_ui.tsx        # React component for streaming UI
    └── chunk_processor.py      # Process streaming chunks
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with streaming patterns |
| `streaming_client.py` | Python | Streaming search client implementation |
| `sse_handler.py` | Python | SSE handling for streaming responses |
| `streaming_ui.tsx` | React/TSX | UI component for streaming display |
| `chunk_processor.py` | Python | Process and aggregate streaming chunks |

## Summary

**Category:** cicd
**Target Audience:** Developer building real-time apps
**Trigger Phrases:** `perplexity streaming`, `perplexity real-time`, `perplexity live search`, `stream perplexity`

### What This Skill Does

This skill teaches streaming search implementation:

- Enabling streaming mode in API requests
- Handling Server-Sent Events (SSE)
- Processing streaming chunks
- Building responsive UI with streaming
- Error handling during streams

### Technical Success Criteria

- Smooth streaming with proper chunk handling
- SSE connection managed correctly
- Partial results displayed incrementally

### Business Success Criteria

- Responsive user experience
- Perceived performance improvement
- Interactive search interfaces

## Related Skills

- `perplexity-sdk-patterns` - Client patterns for streaming
- `perplexity-citation-handling` - Citations in streamed responses
- `perplexity-rate-limits` - Rate limits with streaming
