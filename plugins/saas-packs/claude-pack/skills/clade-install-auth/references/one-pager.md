# clade-install-auth — One-Pager

Install the Anthropic SDK and configure API key authentication in three steps.

## The Problem

Every Claude integration starts with the same setup: install the SDK, configure the API key securely, and verify the connection works. Getting any of these wrong — hardcoded keys, wrong package name, missing environment variable — blocks all downstream work and creates security risks.

## The Solution

This skill provides a three-step setup for both TypeScript and Python: install the SDK package, configure the API key via environment variable (with security warnings against hardcoding), and run a verification call that confirms end-to-end connectivity. Includes advanced configuration for proxies and explicit key injection.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Any developer starting a new Claude integration in TypeScript or Python |
| **What** | SDK installation, API key configuration via environment variables, and a verification call |
| **When** | At the very start of a project — before `clade-hello-world` or any other Claude API skill |

## Key Features

1. **Dual Language Support** — Complete setup for both `@claude-ai/sdk` (npm) and `anthropic` (pip) with identical patterns
2. **Secure Key Configuration** — Environment variable setup with explicit warnings against hardcoding, plus `.env` file option
3. **Connection Verification** — A minimal API call that confirms your key, network, and SDK are all working before you start building

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
