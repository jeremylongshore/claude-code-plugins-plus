# perplexity-sdk-patterns

> Implement common SDK patterns for Perplexity integration

## Directory Structure

```
perplexity-sdk-patterns/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── client_wrapper.py       # Production-ready client wrapper
    ├── async_client.py         # Async/await implementation
    ├── retry_handler.py        # Retry logic with exponential backoff
    └── client_config.yaml      # Configuration options
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with SDK patterns |
| `client_wrapper.py` | Python | Production-ready Perplexity client class |
| `async_client.py` | Python | Async implementation for concurrent requests |
| `retry_handler.py` | Python | Retry logic with exponential backoff |
| `client_config.yaml` | YAML | Client configuration template |

## Summary

**Category:** onboarding
**Target Audience:** Developer building production apps
**Trigger Phrases:** `perplexity sdk`, `perplexity client`, `perplexity patterns`, `perplexity production code`

### What This Skill Does

This skill teaches production SDK patterns for Perplexity:

- Creating reusable client wrappers
- Implementing async/await for concurrent requests
- Error handling with retries and backoff
- Connection pooling and timeout management
- OpenAI SDK compatibility leveraging

### Technical Success Criteria

- Robust client with proper error handling and retries
- Async support for concurrent operations
- Proper timeout and connection management

### Business Success Criteria

- Production-ready integration with reliable operation
- Maintainable codebase with consistent patterns
- Reduced development time for new features

## Related Skills

- `perplexity-install-auth` - Authentication foundation
- `perplexity-rate-limits` - Rate limit handling patterns
- `perplexity-streaming-search` - Streaming implementation
