# perplexity-install-auth

> Set up Perplexity API authentication and configure API keys

## Directory Structure

```
perplexity-install-auth/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── auth_setup.py           # Python authentication setup example
    └── verify_connection.py    # Connection verification script
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with trigger phrases, instructions, and code examples |
| `auth_setup.py` | Python | Example script for API key configuration and environment setup |
| `verify_connection.py` | Python | Script to verify API connectivity with test search query |

## Summary

**Category:** onboarding
**Target Audience:** Developer integrating Perplexity
**Trigger Phrases:** `perplexity auth`, `perplexity setup`, `perplexity api key`, `configure perplexity`

### What This Skill Does

This skill guides developers through setting up secure API authentication for Perplexity AI search. It covers:

- API key acquisition from Perplexity platform
- Environment variable configuration for secure key storage
- OpenAI-compatible SDK setup
- Test search query verification
- Best practices for key rotation and management

### Technical Success Criteria

- API key configured and verified with successful test search query
- Environment variables properly set and secured
- SDK configured with Perplexity base URL

### Business Success Criteria

- Secure and functional authentication enabling AI-powered search
- Foundation established for all subsequent Perplexity integrations

## Related Skills

- `perplexity-hello-world` - First search query after auth setup
- `perplexity-sdk-patterns` - Production client patterns with auth
- `perplexity-common-errors` - Troubleshooting 401 authentication errors
