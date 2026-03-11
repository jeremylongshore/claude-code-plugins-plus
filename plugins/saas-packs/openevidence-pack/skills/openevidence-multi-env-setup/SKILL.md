---
name: openevidence-multi-env-setup
description: |
  Configure OpenEvidence across development, staging, and production environments.
  Use when setting up multiple environments, managing environment-specific configurations,
  or implementing environment promotion strategies for clinical AI applications.
  Trigger with phrases like "openevidence environments", "openevidence staging",
  "openevidence dev setup", "multi-environment openevidence".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Multi-Environment Setup

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure and manage OpenEvidence integrations across development, staging, and production environments with proper isolation, secret management, and promotion strategies.

## Prerequisites
- OpenEvidence accounts for each environment
- Separate API keys per environment
- Infrastructure for each environment
- CI/CD pipeline configured

## Environment Strategy

| Environment | API Endpoint | Purpose | Data |
|-------------|--------------|---------|------|
| Development | sandbox.openevidence.com | Local development | Synthetic |
| Staging | sandbox.openevidence.com | Integration testing | Synthetic |
| Production | api.openevidence.com | Live clinical use | Real (PHI) |

## Instructions

### Step 1: Create Environment Configs
Define per-environment settings for baseUrl, timeout, retries, rate limiting, cache TTL, logging level, and feature flags (deepConsult, webhooks, auditLogging).

### Step 2: Build Configuration Loader
Create a config loader that selects the right environment config based on `NODE_ENV`, with env var overrides for apiKey, orgId, baseUrl, and timeout.

### Step 3: Environment-Aware Client Factory
Implement `OpenEvidenceClientFactory` with per-environment singleton instances and test injection support.

### Step 4: Set Up Secret Management
Use `.env` for development, GCP Secret Manager for staging/production. Define secret paths per environment with separate projects.

### Step 5: Create Promotion Workflow
Build GitHub Actions workflow for staging-to-production promotion with version validation, smoke tests, and gradual traffic shifting (10% -> 50% -> 100%).

### Step 6: Implement Health Checks
Create environment-aware health check that validates OpenEvidence connectivity, cache status, and database health.

## Output
- Environment-specific configuration files (dev/staging/prod)
- Configuration loader with env var overrides
- Client factory with per-environment singletons
- Secret management per environment (GCP Secret Manager)
- GitHub Actions promotion workflow
- Health check endpoint

## Error Handling
| Environment Issue | Detection | Resolution |
|-------------------|-----------|------------|
| Wrong API endpoint | Health check fails | Verify baseUrl in config |
| Secret not found | Startup failure | Check Secret Manager permissions |
| Config mismatch | Unexpected behavior | Validate config loading |
| Promotion failure | CI/CD error | Check version tagging |

## Examples

### Environment Config Summary
- **Dev**: sandbox API, no rate limiting, debug logging, cache disabled
- **Staging**: sandbox API, rate limited (60/min), info logging, 30min cache
- **Production**: production API, rate limited (300/min), warn logging, 1hr cache

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence Sandbox](https://sandbox.openevidence.com/)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)