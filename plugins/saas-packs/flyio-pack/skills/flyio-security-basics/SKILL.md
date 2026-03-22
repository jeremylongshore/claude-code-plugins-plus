---
name: flyio-security-basics
description: |
  Apply Fly.io security best practices for secrets management, private networking,
  TLS certificates, and deploy token scoping.
  Trigger: "fly.io security", "fly secrets", "fly.io TLS", "fly.io private network".
allowed-tools: Read, Write, Edit, Bash(fly:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Security Basics

## Overview

Security practices for Fly.io: encrypted secrets management, private networking (6PN), TLS certificate management, deploy token scoping, and WireGuard VPN access.

## Instructions

### Step 1: Secrets Management

```bash
# Set secrets — encrypted at rest, injected as env vars
fly secrets set API_KEY="sk_live_..." DB_PASSWORD="..." -a my-app

# List (values hidden)
fly secrets list -a my-app

# Unset
fly secrets unset OLD_API_KEY -a my-app

# Import from .env file
fly secrets import < .env.production
```

**Key rules:**
- Secrets are encrypted at rest and in transit
- Available as environment variables inside machines
- Setting/unsetting triggers a rolling restart
- Never put secrets in `fly.toml` `[env]` (those are plaintext)

### Step 2: Deploy Token Scoping

```bash
# Per-app deploy token (minimal scope for CI/CD)
fly tokens create deploy -a my-app
# Use in CI: FLY_API_TOKEN=$DEPLOY_TOKEN fly deploy

# Org token (broader scope — avoid if possible)
fly tokens create org

# Read-only token (monitoring only)
fly tokens create readonly -a my-app
```

### Step 3: Custom Domain TLS

```bash
# Add custom domain
fly certs add api.example.com -a my-app

# Check certificate status
fly certs show api.example.com -a my-app

# Fly manages Let's Encrypt certificates automatically
# Force HTTPS in fly.toml:
```

```toml
[http_service]
  force_https = true
```

### Step 4: Private Networking

```bash
# Apps in same org communicate via .internal DNS (encrypted WireGuard mesh)
# No public internet exposure needed for internal services

# Access internal services from local machine via WireGuard
fly wireguard create
# Then connect: my-app.internal:3000
```

### Security Checklist

- [ ] All sensitive values in `fly secrets`, not `[env]`
- [ ] Deploy tokens scoped per-app (not org-wide)
- [ ] `force_https = true` in fly.toml
- [ ] Internal services use `.internal` DNS, no public ports
- [ ] WireGuard for secure local access
- [ ] Secrets rotated on schedule

## Resources

- [Fly Secrets](https://fly.io/docs/reference/secrets/)
- [Private Networking](https://fly.io/docs/networking/private-networking/)
- [TLS Certificates](https://fly.io/docs/networking/custom-domain/)

## Next Steps

For production readiness, see `flyio-prod-checklist`.
