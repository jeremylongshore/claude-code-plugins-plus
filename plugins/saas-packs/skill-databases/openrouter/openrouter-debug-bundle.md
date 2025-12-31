# openrouter-debug-bundle

> Set up comprehensive logging and debugging for OpenRouter

## Directory Structure

```
openrouter-debug-bundle/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 structured_logging.py   # Structured logging setup
    ├── 🐍 request_tracing.py      # Request/response tracing
    └── 🐍 debug_middleware.py     # Debug middleware implementation
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with debugging infrastructure guide |
| `structured_logging.py` | 🐍 Python | JSON structured logging configuration |
| `request_tracing.py` | 🐍 Python | Correlation ID and request tracing |
| `debug_middleware.py` | 🐍 Python | HTTP client middleware for debugging |

## Summary

**Category:** operations
**Target Audience:** Developer investigating issues
**Trigger Phrases:** `openrouter debug`, `openrouter logging`, `openrouter trace`, `troubleshoot openrouter requests`

### What This Skill Does

This skill establishes comprehensive debugging infrastructure for OpenRouter integrations. It covers:

- Structured JSON logging setup
- Request/response logging with token sanitization
- Correlation IDs for request tracing
- Model and provider tracking
- Performance timing metrics
- Integration with monitoring systems

### Technical Success Criteria

- Structured logging with request tracing
- Model and provider attribution
- Performance metrics captured

### Business Success Criteria

- Faster debugging and issue identification
- Reduced mean time to resolution (MTTR)
- Better operational visibility

## Related Skills

- `openrouter-common-errors` - Error identification from logs
- `openrouter-usage-analytics` - Usage analytics from logs
- `openrouter-audit-logging` - Compliance audit logging
