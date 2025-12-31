# firecrawl-debug-bundle

## Skill Scaffold

```
firecrawl-debug-bundle/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Collect comprehensive diagnostic information for FireCrawl support tickets including request/response logs, configuration, and network tests.
**Workflow:** Support preparation skill - creates complete diagnostic packages for escalation.
**Relates to:** Follows firecrawl-common-errors when self-service fails; feeds into firecrawl-advanced-troubleshooting

## Summary

This skill generates a comprehensive debug bundle for FireCrawl issues that can't be resolved through common error fixes. It collects environment information (SDK version, Node/Python version, OS), sanitized API configuration, sample requests and responses, network connectivity tests to FireCrawl endpoints, and relevant log excerpts. The bundle is formatted for efficient support ticket submission and rapid issue resolution.
