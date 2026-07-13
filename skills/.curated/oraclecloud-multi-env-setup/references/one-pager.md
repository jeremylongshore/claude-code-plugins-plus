# oraclecloud-multi-env-setup — One-Pager

Configure multi-environment OCI workflows with config profiles and compartment-per-environment patterns.

## The Problem

OCI has no "accounts" like AWS — you use compartments + OCI config profiles for dev/staging/prod. But profile switching is manual, compartment OCIDs are easy to confuse, and one wrong `--compartment-id` deploys to production. There's no built-in guardrail to prevent a developer from running a destructive command against the wrong environment.

## The Solution

This skill sets up named config profiles (DEV, STAGING, PROD) in `~/.oci/config`, builds an environment configuration module that maps profiles to compartment OCIDs, creates an environment-aware client factory with safety guardrails (blocking destructive operations in prod), adds CLI shell aliases for safe profile switching, and includes config validation for CI/CD pipelines.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and platform teams managing multiple OCI environments from a single tenancy |
| **What** | Multi-profile OCI config, environment-aware Python client factory, CLI aliases, and deployment guardrails |
| **When** | Setting up dev/staging/prod separation, onboarding new team members, or building CI/CD pipelines that deploy to OCI |

## Key Features

1. **Multi-profile config** — Named profiles in `~/.oci/config` with separate API keys per environment for isolation
2. **Environment-aware client factory** — Python module coupling profiles to compartment OCIDs with destructive operation blocking for prod
3. **Config validation** — Profile-by-profile authentication testing and CI/CD environment variable support

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
