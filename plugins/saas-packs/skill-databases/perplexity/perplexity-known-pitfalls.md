# perplexity-known-pitfalls

> Avoid common mistakes when using Perplexity

## Directory Structure

```
perplexity-known-pitfalls/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── pitfalls_guide.md       # Comprehensive pitfalls documentation
    ├── anti_patterns.py        # Common anti-patterns to avoid
    ├── best_practices.py       # Best practice implementations
    └── migration_tips.md       # Pitfalls when migrating from other APIs
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with pitfall avoidance |
| `pitfalls_guide.md` | Markdown | Document common pitfalls and solutions |
| `anti_patterns.py` | Python | Examples of what NOT to do |
| `best_practices.py` | Python | Correct implementation patterns |
| `migration_tips.md` | Markdown | Avoid pitfalls when migrating |

## Summary

**Category:** advanced
**Target Audience:** Developer troubleshooting
**Trigger Phrases:** `perplexity mistakes`, `perplexity problems`, `perplexity issues`, `avoid perplexity errors`

### What This Skill Does

This skill helps avoid common Perplexity mistakes:

- Over-relying on cached results
- Ignoring citation validation
- Improper error handling
- Rate limit violations
- Query formulation mistakes
- Response parsing errors

### Technical Success Criteria

- Avoided common mistakes and implemented best practices
- Code follows recommended patterns
- Edge cases properly handled

### Business Success Criteria

- Reduced errors and improved reliability
- Faster development through avoided issues
- Higher quality search integrations

## Related Skills

- `perplexity-common-errors` - Error handling
- `perplexity-prod-checklist` - Pre-launch verification
- `perplexity-testing-framework` - Test for pitfalls
