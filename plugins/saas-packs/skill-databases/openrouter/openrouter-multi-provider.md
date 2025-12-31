# openrouter-multi-provider

> Leverage multiple AI providers through OpenRouter unified interface

## Directory Structure

```
openrouter-multi-provider/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 provider_abstraction.py # Provider-agnostic client wrapper
    ├── 🐍 provider_health.py      # Per-provider health monitoring
    └── ⚙️ providers_config.yaml   # Provider preferences and settings
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with multi-provider patterns |
| `provider_abstraction.py` | 🐍 Python | Unified interface across providers |
| `provider_health.py` | 🐍 Python | Monitor provider availability and latency |
| `providers_config.yaml` | ⚙️ YAML | Provider priorities and preferences |

## Summary

**Category:** advanced
**Target Audience:** Developer diversifying providers
**Trigger Phrases:** `openrouter multi-provider`, `openrouter providers`, `openrouter fallback`, `openrouter routing`

### What This Skill Does

This skill teaches multi-provider strategies through OpenRouter:

- Access 100+ models from multiple providers
- Provider-agnostic client abstraction
- Provider health monitoring
- Automatic provider failover
- Cost comparison across providers
- Feature parity considerations

### Technical Success Criteria

- Multiple providers accessible through single interface
- Failover working correctly across providers
- Provider health actively monitored

### Business Success Criteria

- Reduced vendor lock-in risk
- Access to best models from each provider
- High availability through provider diversity

## Related Skills

- `openrouter-fallback-config` - Cross-provider fallback
- `openrouter-model-catalog` - Provider model listing
- `openrouter-model-availability` - Availability monitoring
