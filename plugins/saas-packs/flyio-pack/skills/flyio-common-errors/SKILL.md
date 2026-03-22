---
name: flyio-common-errors
description: |
  Diagnose and fix common Fly.io errors including deployment failures, health check
  failures, machine issues, and networking problems.
  Trigger: "fly.io error", "fly deploy failed", "fly.io not working", "fly health check".
allowed-tools: Read, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Common Errors

## Overview

Quick reference for the most common Fly.io deployment and runtime errors with solutions.

## Error Reference

### Health Check Failed

```
Error: health checks for machine e784... failed
```

**Causes:** App not listening on correct port, slow startup, missing dependencies.

**Fix:**
```bash
# Check logs for startup errors
fly logs -a my-app

# Verify internal_port matches your app
grep internal_port fly.toml

# SSH in and test manually
fly ssh console -C "curl localhost:3000/health"

# Increase health check grace period
```
```toml
# fly.toml — give app more time to start
[http_service.checks]
  grace_period = "30s"
  interval = "15s"
  timeout = "5s"
```

### Deployment Failed — Image Build

```
Error: failed to build: exit code 1
```

**Fix:**
```bash
# Test Docker build locally first
docker build -t test .
docker run -p 3000:3000 test

# Check Dockerfile — common issues:
# - Missing EXPOSE directive
# - Wrong WORKDIR
# - npm install before COPY (layer caching)
```

### Machine Won't Start

```
Error: machine e784... failed to start
```

**Fix:**
```bash
# Check machine events
fly machine status e784...

# Common cause: OOM — increase memory
fly scale vm shared-cpu-1x --memory 512

# Or check for crash loops in logs
fly logs --instance e784...
```

### Connection Refused on .internal

```
Error: connection refused my-api.internal:3000
```

**Fix:**
```bash
# Verify target app is running
fly status -a my-api

# Check the app listens on correct port
fly ssh console -a my-api -C "ss -tlnp"

# Ensure apps are in same organization
fly orgs list
```

### Volume Mount Failures

```
Error: volume vol_xxx not found in region iad
```

**Fix:**
```bash
# Volume must be in same region as machine
fly volumes list -a my-app  # Check region
fly volumes create data --size 10 --region iad  # Match region
```

### Rate Limited by Machines API

```
HTTP 429 Too Many Requests
```

**Fix:** Implement backoff. See `flyio-rate-limits`.

## Quick Diagnostic Commands

```bash
fly status -a my-app              # App and machine status
fly logs -a my-app                # Recent logs
fly machine list -a my-app        # All machines
fly ssh console -a my-app         # Shell access
fly doctor                        # Check flyctl health
fly platform status               # Fly.io platform status
```

## Resources

- [Fly.io Status](https://status.flyio.net/)
- [Fly.io Community](https://community.fly.io/)
- [Fly Docs](https://fly.io/docs/)

## Next Steps

For comprehensive debugging, see `flyio-debug-bundle`.
