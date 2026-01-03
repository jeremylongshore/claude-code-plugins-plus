# openrouter-model-routing

> Implement intelligent model routing based on request characteristics

## Directory Structure

```
openrouter-model-routing/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 content_router.py       # Content-based routing logic
    ├── 🐍 budget_router.py        # Cost-aware model selection
    └── ⚙️ routing_rules.yaml      # Routing configuration rules
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with routing patterns |
| `content_router.py` | 🐍 Python | Route by task type, complexity, content |
| `budget_router.py` | 🐍 Python | Budget-aware model selection |
| `routing_rules.yaml` | ⚙️ YAML | Declarative routing rule configuration |

## Summary

**Category:** advanced
**Target Audience:** Developer optimizing selection
**Trigger Phrases:** `openrouter routing`, `openrouter model selection`, `smart routing openrouter`, `route by task`

### What This Skill Does

This skill teaches intelligent model routing techniques:

- Content-based routing (coding vs creative vs analysis)
- Cost-quality tradeoff optimization
- Latency-aware model selection
- User tier-based routing
- A/B testing model performance
- Dynamic routing based on load

### Technical Success Criteria

- Requests routed to optimal model per task type
- Routing rules configurable without code changes
- Cost savings demonstrated and measured

### Business Success Criteria

- Cost savings through smart routing
- Quality maintained for critical requests
- Flexible model selection per use case

## Related Skills

- `openrouter-routing-rules` - Detailed rule configuration
- `openrouter-model-catalog` - Model capabilities
- `openrouter-fallback-config` - Failover routing
