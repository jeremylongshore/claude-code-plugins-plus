# perplexity-model-selection

> Explore Perplexity model options and select optimal configuration

## Directory Structure

```
perplexity-model-selection/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── model_comparison.py     # Compare different Sonar models
    ├── model_guide.md          # Model selection decision guide
    └── benchmark_queries.py    # Benchmark queries across models
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with model selection guidance |
| `model_comparison.py` | Python | Script to compare Sonar model outputs |
| `model_guide.md` | Markdown | Decision tree for model selection |
| `benchmark_queries.py` | Python | Benchmark performance across models |

## Summary

**Category:** onboarding
**Target Audience:** Developer choosing models
**Trigger Phrases:** `perplexity models`, `sonar model`, `perplexity model selection`, `which perplexity model`

### What This Skill Does

This skill helps developers select the optimal Perplexity model:

- Overview of Sonar model family (sonar-small, sonar-medium, sonar-large)
- Understanding model capabilities and trade-offs
- Cost vs performance analysis
- Use case recommendations
- Online vs offline model considerations

### Technical Success Criteria

- Understanding of available models and their characteristics
- Ability to select appropriate model for use case
- Knowledge of model-specific parameters

### Business Success Criteria

- Optimal model selection balancing speed, accuracy, and cost
- Appropriate model for business requirements
- Cost-effective model usage

## Related Skills

- `perplexity-pricing-usage` - Cost implications of model selection
- `perplexity-sdk-patterns` - Implementing model selection in code
- `perplexity-pro-features` - Pro-tier model access
