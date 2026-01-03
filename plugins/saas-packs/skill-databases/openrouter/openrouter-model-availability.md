# openrouter-model-availability

> Monitor and handle model availability and fallbacks

## Directory Structure

```
openrouter-model-availability/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 availability_monitor.py # Model availability monitoring
    ├── 🐍 health_checker.py       # Model health checking
    └── 🐍 fallback_handler.py     # Automatic fallback handling
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with model availability guide |
| `availability_monitor.py` | 🐍 Python | Monitor model availability status |
| `health_checker.py` | 🐍 Python | Check model health and latency |
| `fallback_handler.py` | 🐍 Python | Handle model unavailability |

## Summary

**Category:** operations
**Target Audience:** Developer handling model outages
**Trigger Phrases:** `openrouter availability`, `openrouter model down`, `openrouter fallback`, `openrouter outage`

### What This Skill Does

This skill teaches monitoring and handling model availability issues. It covers:

- Model status API endpoint
- Health check patterns
- Availability monitoring
- Automatic fallback triggering
- Provider outage handling
- Recovery detection

### Technical Success Criteria

- Automatic failover to alternative models
- Health monitoring implemented
- Recovery detection working

### Business Success Criteria

- Continuous service availability
- Minimal user impact during outages
- Transparent provider switching

## Related Skills

- `openrouter-fallback-config` - Configuring fallback chains
- `openrouter-multi-provider` - Using multiple providers
- `openrouter-model-routing` - Dynamic model selection
