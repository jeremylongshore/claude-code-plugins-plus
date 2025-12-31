# openrouter-install-auth

> Set up OpenRouter API authentication and configure API keys

## Directory Structure

```
openrouter-install-auth/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    └── 🐍 auth_setup.py           # Python authentication setup example
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with trigger phrases, instructions, and code examples |
| `auth_setup.py` | 🐍 Python | Example script for API key configuration and verification |

## Summary

**Category:** onboarding
**Target Audience:** Developer integrating OpenRouter
**Trigger Phrases:** `openrouter auth`, `openrouter setup`, `openrouter api key`, `configure openrouter`

### What This Skill Does

This skill guides developers through setting up secure API authentication for OpenRouter multi-model gateway. It covers:

- API key acquisition from OpenRouter platform
- Environment variable configuration
- OpenAI SDK compatibility setup
- Test request verification
- HTTP-Referer header configuration for app identification

### Technical Success Criteria

- API key configured and verified with successful test request
- OpenAI SDK configured with OpenRouter base URL
- Environment variables properly set

### Business Success Criteria

- Secure and functional authentication enabling multi-model access
- Foundation established for all subsequent OpenRouter integrations

## Related Skills

- `openrouter-hello-world` - First API request after auth setup
- `openrouter-sdk-patterns` - Production client patterns with auth
- `openrouter-common-errors` - Troubleshooting 401 authentication errors
