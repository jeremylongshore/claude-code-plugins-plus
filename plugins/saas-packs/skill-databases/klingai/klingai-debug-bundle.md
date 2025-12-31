# klingai-debug-bundle

> Set up comprehensive logging and debugging for Kling AI

## Directory Structure

```
klingai-debug-bundle/
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
**Trigger Phrases:** `klingai debug`, `kling ai logging`, `klingai trace`, `troubleshoot klingai requests`

### What This Skill Does

This skill establishes comprehensive debugging infrastructure for Kling AI integrations. It covers:

- Structured JSON logging setup
- Request/response logging with sanitization
- Correlation IDs for request tracing
- Performance timing metrics
- Debug levels and log filtering
- Integration with monitoring systems

### Technical Success Criteria

- Structured logging with request tracing
- Correlation IDs linking related operations
- Performance metrics captured

### Business Success Criteria

- Faster debugging and issue identification
- Reduced mean time to resolution (MTTR)
- Better operational visibility

## Related Skills

- `klingai-common-errors` - Error identification from logs
- `klingai-job-monitoring` - Job-level monitoring
- `klingai-audit-logging` - Compliance audit logging
