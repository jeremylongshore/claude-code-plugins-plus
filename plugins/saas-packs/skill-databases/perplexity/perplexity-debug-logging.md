# perplexity-debug-logging

> Set up comprehensive logging and debugging for Perplexity

## Directory Structure

```
perplexity-debug-logging/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── logging_config.py       # Structured logging setup
    ├── request_tracer.py       # Request/response tracing
    ├── debug_middleware.py     # Debug middleware for requests
    └── log_format.json         # Structured log format template
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with logging patterns |
| `logging_config.py` | Python | Configure structured logging |
| `request_tracer.py` | Python | Trace requests through the system |
| `debug_middleware.py` | Python | Middleware for request debugging |
| `log_format.json` | JSON | Structured log format specification |

## Summary

**Category:** operations
**Target Audience:** Developer investigating issues
**Trigger Phrases:** `perplexity logging`, `perplexity debug`, `perplexity trace`, `perplexity logs`

### What This Skill Does

This skill teaches comprehensive logging for Perplexity:

- Structured logging configuration
- Request/response logging with timing
- Correlation IDs for request tracing
- Log levels and filtering
- Sensitive data redaction

### Technical Success Criteria

- Structured logging with request tracing
- Request/response pairs logged with correlation IDs
- Performance metrics captured

### Business Success Criteria

- Faster debugging and issue identification
- Audit trail for operations
- Proactive issue detection

## Related Skills

- `perplexity-common-errors` - Using logs for troubleshooting
- `perplexity-monitoring-alerts` - Alerting on log patterns
- `perplexity-audit-logging` - Compliance logging requirements
