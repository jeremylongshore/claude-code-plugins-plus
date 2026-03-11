---
name: evernote-multi-env-setup
description: |
  Configure multi-environment setup for Evernote integrations.
  Use when setting up dev, staging, and production environments,
  or managing environment-specific configurations.
  Trigger with phrases like "evernote environments", "evernote staging",
  "evernote dev setup", "multiple environments evernote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Multi-Environment Setup

## Overview
Configure separate development, staging, and production environments for Evernote integrations with proper isolation and configuration management.

## Prerequisites
- Multiple Evernote API keys (sandbox and production)
- Environment management infrastructure
- CI/CD pipeline

## Instructions

### Step 1: Environment Configuration Files

### Step 2: Environment Variables

### Step 3: Configuration Loader

### Step 4: Environment-Aware Client Factory

### Step 5: Docker Compose for Local Development

### Step 6: Environment-Specific Middleware

### Step 7: CI/CD Environment Configuration

### Step 8: Environment Health Check

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Environment-specific configuration files
- Configuration loader with environment variable support
- Environment-aware client factory
- Docker Compose for local development
- CI/CD environment configuration
- Health check endpoints

## Resources
- [12 Factor App - Config](https://12factor.net/config)
- [Evernote Sandbox](https://sandbox.evernote.com)
- [Docker Compose](https://docs.docker.com/compose/)

## Next Steps
For observability setup, see `evernote-observability`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Evernote Multi Env Setup |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote multi env setup for production environments with multiple constraints and team-specific requirements.