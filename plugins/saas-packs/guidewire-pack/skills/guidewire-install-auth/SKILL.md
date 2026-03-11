---
name: guidewire-install-auth
description: |
  Install and configure Guidewire InsuranceSuite development environment and Cloud API authentication.
  Use when setting up a new Guidewire integration, configuring OAuth2 credentials,
  registering with Guidewire Hub, or initializing Guidewire Studio.
  Trigger with phrases like "install guidewire", "setup guidewire",
  "guidewire auth", "configure guidewire API", "guidewire cloud credentials".
allowed-tools: Read, Write, Edit, Bash(java:*), Bash(gradle:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Install & Auth

## Overview

Set up Guidewire InsuranceSuite development environment and configure Cloud API authentication with Guidewire Hub using OAuth2 and JWT tokens.

## Prerequisites

- JDK 11 or 17 (Guidewire Cloud 202503+ requires JDK 17)
- Gradle 7.x or 8.x
- Guidewire Cloud account with developer access
- Access to Guidewire Cloud Console (GCC)
- Guidewire Hub registration for your application

## Instructions

### Step 1: Install Development Tools

### Step 2: Configure Guidewire Studio

### Step 3: Register Application with Guidewire Hub

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

1. Log into Guidewire Cloud Console (GCC) at `https://gcc.guidewire.com`
2. Navigate to **Identity & Access > Applications**
3. Click **Register Application**
4. Select application type:
   - **Browser Application** - For Jutro frontends (OAuth2 Authorization Code flow)
   - **Service Application** - For backend integrations (OAuth2 Client Credentials flow)
5. Record the `client_id` and `client_secret`

### Step 4: Configure OAuth2 Credentials

### Step 5: Obtain Access Token (Service Application)

### Step 6: Verify Connection

## Gosu Authentication (Server-Side)

## Output

- Configured Guidewire Studio project
- OAuth2 credentials in environment variables
- Verified connection to Cloud API endpoints
- JWT token acquisition working

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client credentials | Verify client_id and secret in GCC |
| `invalid_scope` | Unauthorized scope requested | Check API role assignments in GCC |
| `401 Unauthorized` | Expired or invalid token | Refresh token, check clock sync |
| `403 Forbidden` | Missing API role permissions | Assign appropriate API roles in GCC |
| `PKIX path building failed` | SSL certificate issue | Import Guidewire CA certificates |

## API Roles Configuration

Configure in Guidewire Cloud Console:

## Examples

### Complete TypeScript Client Setup

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Authentication](https://docs.guidewire.com/education/cloud-integration-basics/latest/docs/authentication/cloud_api_auth/)
- [Guidewire Hub Registration](https://docs.guidewire.com/cloud/pc/202503/cloudapica/cloudAPI/topics/702-AuthFlows/)
- [Guidewire Cloud Console](https://gcc.guidewire.com/)

## Next Steps

After successful auth, proceed to `guidewire-hello-world` for your first API calls.