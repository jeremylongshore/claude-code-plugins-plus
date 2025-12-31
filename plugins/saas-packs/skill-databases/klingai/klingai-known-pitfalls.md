# klingai-known-pitfalls

> Avoid common mistakes when using Kling AI

## Directory Structure

```
klingai-known-pitfalls/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 anti_patterns.py        # Common anti-patterns to avoid
    ├── 🐍 best_practices.py       # Best practice implementations
    └── 📄 checklist.md            # Pre-launch pitfall checklist
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with common pitfalls and solutions |
| `anti_patterns.py` | 🐍 Python | Examples of what NOT to do |
| `best_practices.py` | 🐍 Python | Correct implementations |
| `checklist.md` | 📄 Markdown | Checklist to avoid pitfalls |

## Summary

**Category:** advanced
**Target Audience:** Developer troubleshooting
**Trigger Phrases:** `klingai pitfalls`, `kling ai mistakes`, `klingai gotchas`, `klingai best practices`

### What This Skill Does

This skill documents common mistakes and pitfalls when working with Kling AI. It covers:

- Not handling async jobs (expecting immediate results)
- Ignoring rate limits
- Poor error handling
- Hardcoding API keys
- Not validating prompts
- Ignoring video URL expiration
- Blocking main thread while polling
- Not tracking costs
- Poor prompt engineering
- Not testing before production

### Technical Success Criteria

- Avoided common mistakes and implemented best practices
- Code reviewed against pitfall checklist
- Anti-patterns identified and refactored

### Business Success Criteria

- Reduced errors and improved reliability
- Faster time to production
- Lower support burden

## Related Skills

- `klingai-common-errors` - Error handling patterns
- `klingai-sdk-patterns` - Correct implementation patterns
- `klingai-prod-checklist` - Pre-production verification
