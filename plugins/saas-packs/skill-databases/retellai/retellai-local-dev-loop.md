# retellai-local-dev-loop

> Configure Retell AI local development with webhook tunneling, testing, and fast iteration cycles

## Directory Structure

```
retellai-local-dev-loop/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for local development environment setup |
| examples/example.py | Python | Example showing local webhook server with ngrok tunnel configuration |

## Summary

**Category:** onboarding
**Target Audience:** Voice AI developers, Full-stack developers
**Trigger Phrases:** `retell dev setup`, `retell local development`, `retell dev environment`, `develop with retell`

### What This Skill Does

This skill configures a complete local development environment for Retell AI voice agent development. It sets up webhook tunneling using ngrok to receive call events locally, configures environment variables for different stages, and establishes a fast iteration cycle for testing agent behavior without deploying to production.

### Technical Success Criteria

- Working development environment with webhook reception
- ngrok tunnel configured and connected to Retell AI
- Environment variable management for local vs production
- Test suite for validating agent responses

### Business Success Criteria

- Faster development cycles for voice agents
- Improved developer productivity
- Achieve sub-minute test cycles for Retell AI voice agent development

## Related Skills

- retellai-install-auth - Prerequisite for SDK setup
- retellai-webhook-server - Production webhook deployment
- retellai-agent-creation - Creating agents to test locally
