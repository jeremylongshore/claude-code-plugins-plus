# replit-debug-bundle

## Skill Scaffold

```
replit-debug-bundle/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Collect comprehensive diagnostic information for Replit support including logs, config, and resource usage.
**Workflow:** Support escalation skill - creates detailed diagnostic package when self-service troubleshooting fails.
**Relates to:** Follows replit-common-errors when issues persist; informs replit-observability.

## Summary

This skill creates a comprehensive debug bundle for Replit support escalation. It collects console logs and error output, replit.nix and .replit configuration files, package.json or requirements.txt dependencies, resource usage metrics (CPU, memory, storage), network connectivity test results, environment information (language version, OS), and recent file changes. The bundle is formatted for easy sharing with Replit support to accelerate issue resolution.
