# perplexity-response-validation

> Validate and verify Perplexity search responses

## Directory Structure

```
perplexity-response-validation/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── response_validator.py   # Response validation logic
    ├── quality_scorer.py       # Response quality scoring
    ├── schema_validator.py     # JSON schema validation
    └── validation_rules.yaml   # Configurable validation rules
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with validation patterns |
| `response_validator.py` | Python | Validate response structure and content |
| `quality_scorer.py` | Python | Score response quality and relevance |
| `schema_validator.py` | Python | JSON schema validation for responses |
| `validation_rules.yaml` | YAML | Configurable validation rules |

## Summary

**Category:** operations
**Target Audience:** Developer ensuring quality
**Trigger Phrases:** `perplexity validate`, `perplexity quality`, `perplexity verify`, `perplexity check response`

### What This Skill Does

This skill teaches response validation for Perplexity:

- Response structure validation
- Citation completeness checks
- Content quality scoring
- Relevance verification
- Empty or error response detection

### Technical Success Criteria

- Responses validated for completeness and accuracy
- Quality scoring implemented and calibrated
- Invalid responses detected and handled

### Business Success Criteria

- High-quality search results for users
- Reduced downstream errors
- Confidence in search accuracy

## Related Skills

- `perplexity-citation-handling` - Validate citations specifically
- `perplexity-common-errors` - Handle validation failures
- `perplexity-testing-framework` - Test response validation
