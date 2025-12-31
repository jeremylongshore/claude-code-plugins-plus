# exa-install-auth

## Skill Scaffold

```
exa-install-auth/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Install and configure Exa SDK authentication including API key setup, environment variable configuration (EXA_API_KEY), and connection verification.
**Workflow:** First skill in the onboarding sequence - sets up foundational SDK and authentication before any other Exa operations can be performed.
**Relates to:** Prerequisite for exa-hello-world and all other skills; security patterns build on exa-security-basics

## Summary

This skill handles the initial setup of Exa SDK and authentication. It guides developers through installing the appropriate SDK package (npm: exa-js or pip: exa_py), configuring API keys via environment variables or .env files, and verifying the connection works correctly with a test search. This is the essential first step before any neural search development can begin.
