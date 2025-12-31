# openrouter-performance-tuning

> Optimize OpenRouter performance for speed and quality

## Directory Structure

```
openrouter-performance-tuning/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 latency_optimizer.py    # Request latency optimization
    ├── 🐍 throughput_manager.py   # Concurrent request handling
    └── 🐍 benchmark_suite.py      # Performance benchmarking tools
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with performance patterns |
| `latency_optimizer.py` | 🐍 Python | Minimize time to first token |
| `throughput_manager.py` | 🐍 Python | Maximize concurrent request capacity |
| `benchmark_suite.py` | 🐍 Python | Measure and track performance metrics |

## Summary

**Category:** advanced
**Target Audience:** Performance engineer
**Trigger Phrases:** `openrouter performance`, `optimize openrouter`, `openrouter latency`, `openrouter throughput`

### What This Skill Does

This skill teaches OpenRouter performance optimization:

- Time to first token optimization
- Connection pooling and keep-alive
- Concurrent request batching
- Streaming for perceived latency
- Model selection for speed vs quality
- Geographic endpoint selection

### Technical Success Criteria

- P95 latency reduced by 30%+
- Throughput increased to target levels
- Bottlenecks identified and resolved

### Business Success Criteria

- Improved user experience
- Higher system capacity
- Production performance targets met

## Related Skills

- `openrouter-caching-strategy` - Reduce API calls
- `openrouter-streaming-setup` - Real-time responses
- `openrouter-rate-limits` - Throughput optimization
