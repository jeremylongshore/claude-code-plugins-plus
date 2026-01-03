# openrouter-routing-rules

> Configure intelligent model routing rules

## Directory Structure

```
openrouter-routing-rules/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 routing_engine.py       # Routing engine implementation
    ├── 🐍 rule_evaluator.py       # Rule evaluation logic
    └── 📄 routing_rules.yaml      # Routing rule definitions
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with routing rules guide |
| `routing_engine.py` | 🐍 Python | Implement routing engine |
| `rule_evaluator.py` | 🐍 Python | Evaluate routing rules |
| `routing_rules.yaml` | 📄 YAML | Define routing rules |

## Summary

**Category:** cicd
**Target Audience:** Developer optimizing model selection
**Trigger Phrases:** `openrouter routing`, `openrouter rules`, `model routing`, `smart model selection`

### What This Skill Does

This skill teaches configuring intelligent model routing rules. It covers:

- Cost-based routing (use cheaper models for simple tasks)
- Quality-based routing (premium models for complex tasks)
- Latency-based routing (fast models for real-time)
- Context-length routing (large context models when needed)
- A/B testing with routing
- Rule priority and conflict resolution

### Technical Success Criteria

- Dynamic model selection based on criteria
- Rules properly evaluated per request
- A/B testing infrastructure

### Business Success Criteria

- Optimal cost-quality-speed balance
- Efficient resource utilization
- Data-driven model optimization

## Related Skills

- `openrouter-model-routing` - Request-level routing
- `openrouter-fallback-config` - Fallback as routing
- `openrouter-performance-tuning` - Optimizing routing decisions
