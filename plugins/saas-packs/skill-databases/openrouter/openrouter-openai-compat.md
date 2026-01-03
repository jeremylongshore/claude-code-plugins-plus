# openrouter-openai-compat

> Use OpenRouter with existing OpenAI SDK code

## Directory Structure

```
openrouter-openai-compat/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 migration_guide.py      # OpenAI to OpenRouter migration
    └── 🐍 drop_in_replacement.py  # Drop-in replacement patterns
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with OpenAI compatibility guide |
| `migration_guide.py` | 🐍 Python | Step-by-step migration from OpenAI |
| `drop_in_replacement.py` | 🐍 Python | Minimal changes for OpenRouter |

## Summary

**Category:** onboarding
**Target Audience:** Developer migrating from OpenAI
**Trigger Phrases:** `openrouter openai`, `openai to openrouter`, `openrouter compatible`, `migrate to openrouter`

### What This Skill Does

This skill teaches using OpenRouter with existing OpenAI SDK code. It covers:

- OpenAI SDK base_url configuration
- Model name mapping (openai/gpt-4 format)
- API compatibility differences
- Feature parity and limitations
- Drop-in replacement patterns
- Migration best practices

### Technical Success Criteria

- Seamless integration with minimal code changes
- Existing OpenAI code working with OpenRouter
- Model names properly mapped

### Business Success Criteria

- Faster migration with code reuse
- Access to 100+ models through familiar SDK
- Reduced vendor lock-in

## Related Skills

- `openrouter-sdk-patterns` - Production client patterns
- `openrouter-model-catalog` - Available models beyond OpenAI
- `openrouter-multi-provider` - Using multiple providers
