# instantly-multi-env-setup

> Configure Instantly across development, staging, and production environments with proper isolation

## Directory Structure

```
instantly-multi-env-setup/
├── SKILL.md
└── examples/
    ├── env_config.py
    ├── environment_vars.env.example
    ├── workspace_setup.py
    └── env_switcher.sh
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Multi-environment configuration and best practices |
| env_config.py | Python | Environment-aware configuration loader |
| environment_vars.env.example | Env | Template for environment variables per stage |
| workspace_setup.py | Python | Create and configure isolated Instantly workspaces |
| env_switcher.sh | Shell | Switch between environment configurations |

## Summary

**Category:** CI/CD
**Target Audience:** Platform engineers managing multi-environment infrastructure
**Trigger Phrases:** "instantly environments", "staging production instantly", "multi env instantly", "instantly workspace isolation", "dev staging prod instantly"
**Definition of Success (Technical):** Each environment isolated with proper API keys and settings
**Definition of Success (Business):** Safe testing without affecting production campaigns
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
