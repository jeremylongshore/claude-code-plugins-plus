---
description: Scans Docker containers and images for security vulnerabilities
shortcut: dss
category: security
difficulty: intermediate
estimated_time: 5-10 minutes
---

<!-- DESIGN DECISION: Container security as critical infrastructure concern -->
<!-- Containers run in production with elevated privileges, must be secured -->
<!-- Covers both image vulnerabilities and runtime configuration -->

<!-- ALTERNATIVES CONSIDERED: -->
<!-- - Manual Dockerfile review (rejected: time-consuming, inconsistent) -->
<!-- - External tool only (rejected: requires installation, not integrated) -->
<!-- - Image scanning only (rejected: misses runtime configuration issues) -->

<!-- VALIDATION: Tested against intentionally vulnerable containers and real production images -->
<!-- Successfully identified CVEs, privileged containers, exposed secrets, misconfigurations -->

# Docker Security Scan

Comprehensively scans Docker containers and images for vulnerabilities, misconfigurations, and security best practices violations. Identifies CVEs in base images and dependencies, insecure configurations, exposed secrets, and privilege escalation risks.

## What This Command Does

**Complete Container Security Analysis:**
- ✅ Scans images for known CVEs (vulnerabilities in OS packages and dependencies)
- ✅ Detects insecure Dockerfile configurations
- ✅ Identifies exposed secrets (API keys, passwords, tokens)
- ✅ Checks for privileged containers and excessive permissions
- ✅ Validates security best practices (non-root user, minimal base image)
- ✅ Analyzes running containers for runtime security issues

**Output:** Detailed security report with severity-rated findings and remediation steps

**Time:** 5-10 minutes per image/container

---

## When to Use This Command

**Perfect For:**
- Pre-deployment container security validation
- CI/CD pipeline security gates
- Production container audits
- Kubernetes pod security review
- Docker Compose security assessment

**Use This When:**
- Building new container images
- Before deploying to production
- After updating base images
- Regular security audits (weekly/monthly)
- Investigating security incidents

---

## Usage

```bash
# Scan a Docker image
/docker-security-scan myapp:latest

# Scan running container
/docker-security-scan --container myapp-prod

# Scan all images
/docker-security-scan --all-images

# Scan with detailed output
/docker-security-scan myapp:latest --verbose

# Scan and generate report
/docker-security-scan myapp:latest --output report.md
```

**Shortcut:**
```bash
/dss myapp:latest  # Quick scan
```

---

## What Gets Scanned

### 1. Image Vulnerabilities (CVEs)

**Scans For:**
- Operating system package vulnerabilities
- Application dependency vulnerabilities
- Known exploits in installed software
- Outdated packages with security patches available

**Example Findings:**
```
🚨 CRITICAL: CVE-2024-12345 in openssl
Package: openssl 1.1.1k
Severity: Critical (CVSS 9.8)
Impact: Remote code execution via crafted TLS handshake
Fixed in: openssl 1.1.1w

Remediation:
FROM ubuntu:22.04  # Update base image
RUN apt-get update && apt-get upgrade -y openssl
```

**Example Output:**
```
Image: myapp:latest
Base: node:16 (debian:bullseye)

Vulnerabilities Found: 47
  🔴 Critical: 3
  🟠 High: 12
  🟡 Medium: 18
  🔵 Low: 14

Top Critical CVEs:
1. CVE-2024-12345 (openssl) - RCE via TLS
2. CVE-2024-23456 (curl) - Buffer overflow
3. CVE-2024-34567 (libc6) - Privilege escalation
```

### 2. Dockerfile Security Issues

**Checks:**
- Running as root user
- Hardcoded secrets in layers
- Exposed sensitive ports
- Unnecessary packages installed
- Missing health checks
- Outdated base images

**Example Findings:**
```dockerfile
# ❌ BAD: Running as root
FROM node:16
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]  # Runs as root!

# ✅ GOOD: Non-root user
FROM node:16
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
USER node  # Drop to non-root user
CMD ["node", "server.js"]
```

```dockerfile
# ❌ BAD: Hardcoded secrets
FROM node:16
ENV DATABASE_PASSWORD="MySecretPassword123"  # Exposed in image layers!

# ✅ GOOD: Runtime secrets
FROM node:16
# Pass secrets at runtime via environment variables or secrets management
CMD ["node", "server.js"]
```

```dockerfile
# ❌ BAD: Unnecessary packages
FROM ubuntu:latest
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    curl \
    wget \
    vim \
    emacs \
    git \
    # Unnecessary packages increase attack surface!

# ✅ GOOD: Minimal image
FROM node:16-alpine  # Minimal base image
RUN apk add --no-cache curl  # Only necessary packages
```

### 3. Container Runtime Configuration

**Scans For:**
- Privileged containers (`--privileged`)
- Dangerous capabilities (CAP_SYS_ADMIN, CAP_NET_ADMIN)
- Host network mode
- Mounted sensitive host paths
- No resource limits (CPU, memory)

**Example Findings:**
```bash
# ❌ CRITICAL: Privileged container
docker run --privileged myapp:latest
# Allows container to access all host devices, escape container!

# ✅ SAFE: Non-privileged with minimal capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp:latest
```

```bash
# ⚠️ HIGH: Host network mode
docker run --network=host myapp:latest
# Container can access all host network interfaces

# ✅ SAFE: Bridge network
docker run --network=bridge myapp:latest
```

```bash
# 🚨 CRITICAL: Mounting sensitive host paths
docker run -v /etc:/host-etc myapp:latest
# Container can modify host /etc files!

# ✅ SAFE: Specific, read-only mounts
docker run -v /app/data:/data:ro myapp:latest
```

### 4. Exposed Secrets

**Detects:**
- API keys in environment variables
- Passwords in image layers
- Private keys in container filesystem
- Database credentials
- OAuth tokens

**Example Findings:**
```bash
# ❌ CRITICAL: Secrets in environment variables (visible in docker inspect)
docker run -e AWS_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/..." myapp:latest

# ✅ SAFE: Use secrets management
docker run --env-file /secure/secrets.env myapp:latest
# Or use Docker secrets (Swarm) or Kubernetes secrets
```

### 5. Network Exposure

**Checks:**
- Exposed ports (especially dangerous: 22 SSH, 3306 MySQL, 6379 Redis)
- Port mapping to 0.0.0.0 (all interfaces)
- Missing network segmentation

**Example Findings:**
```bash
# ⚠️ HIGH: Database exposed to internet
docker run -p 0.0.0.0:5432:5432 postgres:latest
# PostgreSQL accessible from anywhere!

# ✅ SAFE: Bind to localhost only
docker run -p 127.0.0.1:5432:5432 postgres:latest

# ✅ BETTER: Use Docker network (no external exposure)
docker network create app-network
docker run --network=app-network postgres:latest
```

### 6. Resource Limits

**Checks for:**
- Missing memory limits (risk of OOM killing host)
- Missing CPU limits (risk of resource starvation)
- No restart policy (availability)

**Example Findings:**
```bash
# ⚠️ MEDIUM: No resource limits
docker run myapp:latest
# Can consume all host memory/CPU!

# ✅ SAFE: Resource limits set
docker run \
  --memory=512m \
  --cpus=1.0 \
  --restart=unless-stopped \
  myapp:latest
```

---

## Example: Full Scan Output

```bash
$ /docker-security-scan myapp:latest

🔍 Docker Security Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Image: myapp:latest
📁 Size: 1.2 GB
🏗️  Base: node:16 (debian:bullseye)
📅 Created: 2025-10-05

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL ISSUES (Fix Immediately)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Running as Root User
   📄 Dockerfile:15
   🔴 Severity: Critical

   USER root  # Container runs as root!

   ⚠️  Impact: If container is compromised, attacker has root access

   ✅ Fix:
   RUN addgroup -S appgroup && adduser -S appuser -G appgroup
   USER appuser

2. Hardcoded Database Password
   📄 Dockerfile:8
   🔴 Severity: Critical

   ENV DB_PASSWORD="MySecretPassword123"

   ⚠️  Impact: Password visible in image layers, docker inspect

   ✅ Fix:
   - Remove from Dockerfile
   - Pass at runtime: docker run -e DB_PASSWORD="$SECRET" myapp:latest
   - Use Docker secrets or Kubernetes secrets

3. CVE-2024-12345 in openssl
   📦 Package: openssl 1.1.1k
   🔴 Severity: Critical (CVSS 9.8)

   Vulnerability: Remote code execution via TLS handshake

   ✅ Fix:
   FROM node:16-bullseye  # Use latest base image
   RUN apt-get update && apt-get upgrade -y openssl

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  HIGH SEVERITY ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. Privileged Container Mode
   🟠 Severity: High

   docker run --privileged myapp:latest

   ⚠️  Impact: Container can access all host devices, escape container

   ✅ Fix:
   - Remove --privileged flag
   - Use specific capabilities: --cap-add=NET_BIND_SERVICE

5. Host Network Mode
   🟠 Severity: High

   docker run --network=host myapp:latest

   ⚠️  Impact: Container can access all host network interfaces

   ✅ Fix:
   docker run --network=bridge myapp:latest

6. Mounted Sensitive Host Path
   🟠 Severity: High

   -v /etc:/host-etc

   ⚠️  Impact: Container can read/modify host /etc files

   ✅ Fix:
   - Remove mount if not needed
   - Use specific paths: -v /app/config:/config:ro
   - Mount read-only: :ro

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 MEDIUM SEVERITY ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. No Health Check Defined
   🟡 Severity: Medium

   HEALTHCHECK instruction missing

   ⚠️  Impact: Container may be running but unhealthy

   ✅ Fix:
   HEALTHCHECK --interval=30s --timeout=3s \
     CMD curl -f http://localhost:3000/health || exit 1

8. Outdated Base Image
   🟡 Severity: Medium

   FROM node:16 (2022-04-20)

   ⚠️  Impact: Missing 18 months of security patches

   ✅ Fix:
   FROM node:20-alpine  # Latest LTS, minimal

9. No Resource Limits
   🟡 Severity: Medium

   No --memory or --cpus limits

   ⚠️  Impact: Container can consume all host resources

   ✅ Fix:
   docker run --memory=512m --cpus=1.0 myapp:latest

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 VULNERABILITY SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Issues: 47
 🔴 Critical: 3 (Fix immediately)
 🟠 High: 12 (Fix within 1 week)
 🟡 Medium: 18 (Fix within 1 month)
 🔵 Low: 14 (Best practices)

CVE Summary:
  Critical: 3 CVEs
  High: 12 CVEs
  Medium: 18 CVEs
  Low: 14 CVEs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RECOMMENDED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority 1 (Immediate):
✓ Add non-root user (2 hours)
✓ Remove hardcoded secrets (1 hour)
✓ Update base image (30 min)

Priority 2 (This Week):
✓ Remove privileged mode (1 hour)
✓ Fix host network usage (2 hours)
✓ Review volume mounts (2 hours)

Priority 3 (This Month):
✓ Add health checks (1 hour)
✓ Set resource limits (30 min)
✓ Update all dependencies (3 hours)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 SECURITY BEST PRACTICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Use minimal base images (alpine, distroless)
✅ Run as non-root user
✅ Don't embed secrets in images
✅ Scan images regularly (weekly)
✅ Update base images monthly
✅ Use multi-stage builds (smaller, more secure)
✅ Set resource limits
✅ Add health checks
✅ Use specific image tags (not :latest)
✅ Sign and verify images

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scan completed! ✅
Report saved to: docker-security-scan-2025-10-10.md
```

---

## Secure Dockerfile Template

```dockerfile
# ✅ SECURE DOCKERFILE TEMPLATE

# Use minimal, specific base image (not :latest)
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching)
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production \
    && npm cache clean --force

# Copy application code
COPY . .

# Build application (if needed)
RUN npm run build

# ===== Production Stage =====
FROM node:20-alpine

# Add metadata
LABEL maintainer="[email protected]" \
      version="1.0.0" \
      description="MyApp production image"

# Install security updates
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy built application from build stage
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules

# Switch to non-root user
USER appuser

# Expose port (document only, not publish)
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run application
CMD ["node", "dist/server.js"]
```

---

## Secure Docker Run Command

```bash
docker run \
  --name myapp \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges:true \
  --memory=512m \
  --cpus=1.0 \
  --restart=unless-stopped \
  --network=app-network \
  -p 127.0.0.1:3000:3000 \
  -e NODE_ENV=production \
  --env-file /secure/secrets.env \
  myapp:1.0.0
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Security Scan

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Security Scan
        run: /docker-security-scan myapp:${{ github.sha }} --output report.md

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: report.md

      - name: Fail on Critical Issues
        run: |
          if grep -q "🔴 Critical" report.md; then
            echo "Critical vulnerabilities found!"
            exit 1
          fi
```

---

## Related Commands

- `/security-scan-quick` - General application security scan
- `/api-security-audit` - API-specific security testing
- `/crypto-audit` - Cryptography review

---

## Support

**Found container vulnerabilities?**
1. Fix critical issues immediately (root user, secrets, CVEs)
2. For remediation help: Ask Security Auditor Expert
3. For Docker best practices: Consult Docker security documentation
4. Test fixes: Re-run `/docker-security-scan` after changes

---

**Time Investment:** 5-10 minutes per scan
**Value:** Prevent container escape, data breaches, and production compromises

**Scan containers early. Fix vulnerabilities fast. Deploy securely.** 🐳🔐
