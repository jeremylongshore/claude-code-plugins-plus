# openrouter-load-balancing

> Distribute load across OpenRouter instances

## Directory Structure

```
openrouter-load-balancing/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 load_balancer.py        # Load balancer implementation
    ├── 🐍 health_monitor.py       # Health monitoring
    └── 🐍 circuit_breaker.py      # Circuit breaker pattern
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with load balancing guide |
| `load_balancer.py` | 🐍 Python | Load balancing implementation |
| `health_monitor.py` | 🐍 Python | Monitor endpoint health |
| `circuit_breaker.py` | 🐍 Python | Circuit breaker pattern |

## Summary

**Category:** cicd
**Target Audience:** Developer scaling systems
**Trigger Phrases:** `openrouter load balancing`, `scale openrouter`, `openrouter high availability`, `openrouter distribution`

### What This Skill Does

This skill teaches distributing load for OpenRouter at scale. It covers:

- Multi-key load distribution
- Round-robin and weighted distribution
- Health check integration
- Circuit breaker patterns
- Retry with different keys
- Rate limit distribution

### Technical Success Criteria

- Even distribution with health checks
- Circuit breakers preventing cascading failures
- Rate limits distributed across keys

### Business Success Criteria

- Scalable system architecture
- Higher aggregate rate limits
- Improved availability

## Related Skills

- `openrouter-rate-limits` - Rate limit handling
- `openrouter-fallback-config` - Fallback strategies
- `openrouter-reference-architecture` - Architecture patterns
