# exa-debug-bundle

## Skill Scaffold

```
exa-debug-bundle/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Collect comprehensive diagnostic information for Exa support tickets including logs, configuration, request traces, and environment details.
**Workflow:** Used when common-errors skill doesn't resolve the issue - prepares complete support bundle.
**Relates to:** Follows exa-common-errors; provides input for support escalation

## Summary

This skill creates a comprehensive debug bundle for Exa support tickets. It collects: SDK version and environment info, redacted API configuration (hiding key), sample request/response pairs with timing, error logs and stack traces, network connectivity test results, and reproduction steps. The bundle is packaged as a shareable archive with automatic API key redaction for safe sharing.
