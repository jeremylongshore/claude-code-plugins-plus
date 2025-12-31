# openrouter-common-errors

> Diagnose and fix common OpenRouter API errors

## Directory Structure

```
openrouter-common-errors/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 error_handler.py        # Comprehensive error handling
    └── 🐍 error_catalog.py        # Error code reference
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with error diagnosis and solutions |
| `error_handler.py` | 🐍 Python | Error handling implementation |
| `error_catalog.py` | 🐍 Python | Error code lookup and solutions |

## Summary

**Category:** operations
**Target Audience:** Developer troubleshooting issues
**Trigger Phrases:** `openrouter error`, `openrouter troubleshoot`, `openrouter 400`, `openrouter 429`, `fix openrouter`

### What This Skill Does

This skill provides comprehensive error diagnosis and resolution for OpenRouter API. It covers:

- HTTP status code meanings (400, 401, 403, 429, 500, 503)
- Model-specific error handling
- Provider error propagation
- Error handling code patterns
- Retry strategies for transient errors

### Technical Success Criteria

- Identified and resolved API errors
- Proper error handling implemented
- Retry logic for recoverable errors

### Business Success Criteria

- Reduced downtime and faster issue resolution
- Improved system reliability
- Better developer productivity

## Related Skills

- `openrouter-debug-bundle` - Comprehensive debugging setup
- `openrouter-rate-limits` - Handling 429 errors specifically
- `openrouter-model-availability` - Model-specific errors
