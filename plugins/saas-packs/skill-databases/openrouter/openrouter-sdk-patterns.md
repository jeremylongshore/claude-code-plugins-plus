# openrouter-sdk-patterns

> Implement common SDK patterns for OpenRouter integration

## Directory Structure

```
openrouter-sdk-patterns/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 robust_client.py        # Production-ready client implementation
    ├── 🐍 retry_patterns.py       # Retry and backoff strategies
    └── 🐍 openai_compat.py        # OpenAI SDK compatibility wrapper
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with production SDK patterns |
| `robust_client.py` | 🐍 Python | Production-ready client with error handling |
| `retry_patterns.py` | 🐍 Python | Exponential backoff and retry logic |
| `openai_compat.py` | 🐍 Python | OpenAI SDK wrapper for OpenRouter |

## Summary

**Category:** onboarding
**Target Audience:** Developer building production apps
**Trigger Phrases:** `openrouter sdk`, `openrouter client patterns`, `openrouter production client`, `robust openrouter`

### What This Skill Does

This skill teaches production-ready SDK patterns for OpenRouter integration. It covers:

- OpenAI SDK configuration for OpenRouter
- Robust client class with comprehensive error handling
- Retry logic with exponential backoff
- Timeout configuration
- Structured logging integration
- Multi-model client patterns

### Technical Success Criteria

- Robust client with error handling and retry logic
- OpenAI SDK properly configured for OpenRouter
- Clean resource management

### Business Success Criteria

- Production-ready integration with reliable operation
- Reduced downtime from transient failures
- Maintainable and testable codebase

## Related Skills

- `openrouter-common-errors` - Error handling patterns
- `openrouter-rate-limits` - Rate limit handling in SDK
- `openrouter-openai-compat` - Full OpenAI compatibility
