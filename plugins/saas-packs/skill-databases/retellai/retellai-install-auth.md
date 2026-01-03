# retellai-install-auth

> Install and configure Retell AI SDK authentication including API key setup and connection verification

## Directory Structure

```
retellai-install-auth/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for Retell AI SDK installation and authentication setup |
| examples/example.py | Python | Working example demonstrating Retell AI client initialization and auth verification |

## Summary

**Category:** onboarding
**Target Audience:** Voice AI developers, Full-stack developers, Platform engineers
**Trigger Phrases:** `install retell ai`, `setup retell`, `retell auth`, `configure retell API key`

### What This Skill Does

This skill handles the initial setup of Retell AI SDK and API authentication. It guides developers through installing the Retell AI Python or Node.js SDK, configuring API keys via environment variables or .env files, and verifying the connection works correctly by making a test API call. This is the essential first step before any Retell AI voice agent development can begin.

### Technical Success Criteria

- Installed SDK package (retell-ai-sdk via npm or pip)
- Configured environment variable (RETELL_API_KEY) or .env file
- Successful connection verification output from test API call

### Business Success Criteria

- Reduced setup time for new team members
- Standardized authentication patterns across team
- Complete Retell AI SDK setup in under 5 minutes with verified connection

## Related Skills

- retellai-hello-world - Next step after authentication setup
- retellai-security-basics - Advanced security patterns for API keys
- retellai-local-dev-loop - Setting up full development environment
