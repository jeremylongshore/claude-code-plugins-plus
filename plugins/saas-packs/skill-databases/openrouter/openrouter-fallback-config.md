# openrouter-fallback-config

> Configure model fallback chains for reliability

## Directory Structure

```
openrouter-fallback-config/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 fallback_chain.py       # Fallback chain configuration
    ├── 🐍 smart_fallback.py       # Intelligent fallback logic
    └── 📄 fallback_matrix.json    # Model fallback matrix
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with fallback configuration guide |
| `fallback_chain.py` | 🐍 Python | Configure fallback chains |
| `smart_fallback.py` | 🐍 Python | Intelligent fallback selection |
| `fallback_matrix.json` | 📄 JSON | Model fallback mappings |

## Summary

**Category:** cicd
**Target Audience:** Developer building reliable systems
**Trigger Phrases:** `openrouter fallback`, `openrouter failover`, `openrouter redundancy`, `model fallback`

### What This Skill Does

This skill teaches configuring model fallback chains for reliability. It covers:

- Fallback chain configuration
- Similar-capability model mapping
- Error-based fallback triggers
- Latency-based fallback
- Cost-aware fallback selection
- Fallback metrics and logging

### Technical Success Criteria

- Automatic failover with minimal latency
- Fallback chains properly configured
- Metrics tracking fallback events

### Business Success Criteria

- Zero-downtime model failures
- Consistent service availability
- Cost-effective fallback strategies

## Related Skills

- `openrouter-model-availability` - Detecting when to fallback
- `openrouter-model-routing` - Dynamic model selection
- `openrouter-multi-provider` - Provider-level fallback
