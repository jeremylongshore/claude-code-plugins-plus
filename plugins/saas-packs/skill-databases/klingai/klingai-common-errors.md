# klingai-common-errors

> Diagnose and fix common Kling AI API errors

## Directory Structure

```
klingai-common-errors/
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
**Trigger Phrases:** `klingai error`, `kling ai troubleshoot`, `klingai 400`, `klingai 429`, `fix klingai`

### What This Skill Does

This skill provides comprehensive error diagnosis and resolution for Kling AI API. It covers:

- HTTP status code meanings (400, 401, 403, 429, 500, 503)
- Error response parsing and interpretation
- Common causes and solutions for each error
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

- `klingai-debug-bundle` - Comprehensive debugging setup
- `klingai-rate-limits` - Handling 429 errors specifically
- `klingai-sdk-patterns` - Error handling in SDK
