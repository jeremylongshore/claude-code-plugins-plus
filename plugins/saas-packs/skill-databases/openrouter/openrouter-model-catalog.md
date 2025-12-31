# openrouter-model-catalog

> Explore and query the OpenRouter model catalog programmatically

## Directory Structure

```
openrouter-model-catalog/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    └── 🐍 model_explorer.py       # Python model catalog query script
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with model catalog guide |
| `model_explorer.py` | 🐍 Python | Script for querying and filtering models |

## Summary

**Category:** onboarding
**Target Audience:** Developer evaluating models
**Trigger Phrases:** `openrouter models`, `list openrouter models`, `openrouter model catalog`, `available models openrouter`

### What This Skill Does

This skill helps developers understand and navigate the OpenRouter model catalog. It covers:

- API endpoint for listing 100+ models
- Model categories (OpenAI, Anthropic, Meta, Mistral, Google)
- Pricing comparison per model
- Context window sizes
- Capability filtering (vision, function calling, etc.)
- Model selection criteria

### Technical Success Criteria

- Understanding of available models and their capabilities
- Ability to query and filter model catalog
- Knowledge of pricing differences

### Business Success Criteria

- Optimal model selection for use case requirements
- Cost-effective model choices
- Quality expectations properly set

## Related Skills

- `openrouter-pricing-basics` - Cost implications of model selection
- `openrouter-model-routing` - Dynamic model selection
- `openrouter-performance-tuning` - Optimizing model parameters
