# perplexity-common-errors

> Diagnose and fix common Perplexity API errors

## Directory Structure

```
perplexity-common-errors/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── error_codes.md          # Comprehensive error code reference
    ├── error_handler.py        # Error handling patterns
    ├── diagnostic_script.py    # Diagnose common issues
    └── troubleshooting.md      # Step-by-step troubleshooting guide
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with error handling guidance |
| `error_codes.md` | Markdown | Complete error code reference with solutions |
| `error_handler.py` | Python | Centralized error handling patterns |
| `diagnostic_script.py` | Python | Script to diagnose common issues |
| `troubleshooting.md` | Markdown | Step-by-step troubleshooting guide |

## Summary

**Category:** operations
**Target Audience:** Developer troubleshooting issues
**Trigger Phrases:** `perplexity error`, `perplexity troubleshoot`, `perplexity debug`, `perplexity not working`

### What This Skill Does

This skill helps diagnose and fix Perplexity API errors:

- 400 Bad Request (malformed queries)
- 401 Unauthorized (authentication issues)
- 403 Forbidden (access denied)
- 429 Too Many Requests (rate limiting)
- 500/502/503 Server errors
- Network and timeout issues

### Technical Success Criteria

- Identified and resolved API errors
- Error handling code implemented
- Understanding of error response format

### Business Success Criteria

- Reduced downtime and faster issue resolution
- Self-service troubleshooting capability
- Fewer support escalations

## Related Skills

- `perplexity-install-auth` - Fix 401 authentication errors
- `perplexity-rate-limits` - Handle 429 errors
- `perplexity-debug-logging` - Set up logging for diagnosis
