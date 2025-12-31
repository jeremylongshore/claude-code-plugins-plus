# retellai-debug-bundle

> Collect comprehensive diagnostic information for Retell AI support tickets including logs, config, and call recordings

## Directory Structure

```
retellai-debug-bundle/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for comprehensive diagnostic collection |
| examples/example.py | Python | Example script for automated debug bundle generation |

## Summary

**Category:** operations
**Target Audience:** Support engineers, DevOps engineers, Senior developers
**Trigger Phrases:** `retell debug`, `retell support bundle`, `collect retell logs`, `retell diagnostic`

### What This Skill Does

This skill creates a comprehensive debug bundle for Retell AI support tickets and incident investigation. It collects environment information, SDK version, redacted configuration, recent call logs, webhook delivery status, and network connectivity test results. All sensitive data (API keys, phone numbers) is automatically redacted.

### Technical Success Criteria

- Debug bundle archive created with all required components
- Environment info, SDK version, and config captured
- Recent call logs and webhook events included
- Sensitive data properly redacted
- Network connectivity tests completed

### Business Success Criteria

- Faster support ticket resolution
- Better root cause analysis capabilities
- Generate complete support bundle in under 2 minutes

## Related Skills

- retellai-common-errors - Self-service error resolution
- retellai-advanced-troubleshooting - Deep debugging techniques
- retellai-incident-runbook - Incident response procedures
