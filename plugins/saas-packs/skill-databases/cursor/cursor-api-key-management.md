# cursor-api-key-management

## Skill Scaffold

```
cursor-api-key-management/
    SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Manages API keys and authentication in Cursor for multiple providers (OpenAI, Anthropic, Azure, Google) including secure storage, rotation, and cost management.

**Workflow:** This skill activates when developers want to use their own API keys with Cursor. It covers supported providers, configuration methods, security best practices, cost management, troubleshooting, and team key management.

**Relates to:** cursor-model-selection (model access with keys), cursor-install-auth (initial key setup), cursor-privacy-settings (key security), cursor-usage-analytics (cost tracking)

## Summary

This security skill covers comprehensive API key management for Cursor. It includes why to use own keys (bypass limits, specific models, control costs), supported providers (OpenAI, Anthropic, Azure, Google), configuration methods (UI, settings.json, environment variables), security best practices (no hardcoding, rotation schedules, file permissions), cost management (monitoring, limits, optimization), troubleshooting (invalid key, rate limited, model unavailable), team key management (per-user vs shared), and backup/recovery procedures.
