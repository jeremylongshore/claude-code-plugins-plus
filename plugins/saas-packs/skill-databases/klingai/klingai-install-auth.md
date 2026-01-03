# klingai-install-auth

> Set up Kling AI API authentication and configure API keys

## Directory Structure

```
klingai-install-auth/
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
**Target Audience:** Developer integrating Kling AI
**Trigger Phrases:** `klingai auth`, `kling ai setup`, `klingai api key`, `configure klingai`

### What This Skill Does

This skill guides developers through setting up secure API authentication for Kling AI video generation services. It covers:

- API key acquisition from Kling AI platform
- Environment variable configuration
- Secure credential storage patterns
- Test request verification
- Secrets manager integration (Google Cloud, AWS)

### Technical Success Criteria

- API key configured and verified with successful test request
- Secure storage implemented (environment variables or secrets manager)
- No hardcoded credentials in codebase

### Business Success Criteria

- Secure and functional authentication enabling video generation
- Foundation established for all subsequent Kling AI integrations

## Related Skills

- `klingai-hello-world` - First video generation after auth setup
- `klingai-sdk-patterns` - Production client patterns with auth
- `klingai-common-errors` - Troubleshooting 401 authentication errors
