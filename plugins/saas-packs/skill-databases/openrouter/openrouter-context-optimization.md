# openrouter-context-optimization

> Optimize context window usage for cost and performance efficiency

## Directory Structure

```
openrouter-context-optimization/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 context_manager.py      # Context window management utilities
    ├── 🐍 summarizer.py           # Conversation summarization for context
    └── 🐍 token_counter.py        # Accurate token counting per model
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with context optimization patterns |
| `context_manager.py` | 🐍 Python | Smart context window management |
| `summarizer.py` | 🐍 Python | Progressive summarization techniques |
| `token_counter.py` | 🐍 Python | Token estimation across different models |

## Summary

**Category:** advanced
**Target Audience:** Developer optimizing prompts
**Trigger Phrases:** `openrouter context`, `openrouter tokens`, `reduce openrouter context`, `optimize prompt tokens`

### What This Skill Does

This skill teaches context window optimization techniques:

- Token counting and estimation across models
- Progressive conversation summarization
- Context compression strategies
- System prompt optimization
- Sliding window techniques for long conversations

### Technical Success Criteria

- Context usage reduced by 40%+ without quality degradation
- Token costs optimized across model families
- Summarization maintains conversation coherence

### Business Success Criteria

- Lower per-request costs
- Support longer conversations within budget
- Better cost efficiency for context-heavy workloads

## Related Skills

- `openrouter-pricing-basics` - Token cost understanding
- `openrouter-performance-tuning` - Overall optimization
- `openrouter-caching-strategy` - Response caching
