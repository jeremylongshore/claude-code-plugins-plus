# openrouter-known-pitfalls

> Avoid common mistakes when using OpenRouter

## Directory Structure

```
openrouter-known-pitfalls/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 📝 anti_patterns.md        # Common anti-patterns documented
    ├── 🐍 code_review_checks.py   # Automated anti-pattern detection
    └── 📝 best_practices.md       # Recommended patterns
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with pitfall avoidance |
| `anti_patterns.md` | 📝 Markdown | Documented anti-patterns with fixes |
| `code_review_checks.py` | 🐍 Python | Automated detection of common mistakes |
| `best_practices.md` | 📝 Markdown | Recommended implementation patterns |

## Summary

**Category:** advanced
**Target Audience:** Developer troubleshooting
**Trigger Phrases:** `openrouter mistakes`, `openrouter anti-patterns`, `openrouter pitfalls`, `openrouter what not to do`

### What This Skill Does

This skill helps avoid common OpenRouter integration mistakes:

- Hardcoded API keys and credential exposure
- Missing error handling and retry logic
- Incorrect model ID formats
- Rate limit handling mistakes
- Context window overflow issues
- Synchronous blocking in async contexts

### Technical Success Criteria

- Anti-patterns identified in codebase
- Fixes prioritized and implemented
- Prevention measures in place

### Business Success Criteria

- Fewer production issues
- Better code quality
- Faster code reviews
- Reduced technical debt

## Related Skills

- `openrouter-common-errors` - Error troubleshooting
- `openrouter-sdk-patterns` - Correct patterns
- `openrouter-debug-bundle` - Issue investigation
