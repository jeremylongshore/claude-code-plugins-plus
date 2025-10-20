---
description: Analyze and optimize Docker images for size and build speed
shortcut: do
category: devops
difficulty: advanced
estimated_time: 3 minutes
---

<!-- DESIGN DECISION: Helps reduce bloated Docker images -->
<!-- Docker images often become bloated due to poor layer ordering, unnecessary files,
     dev dependencies in production, etc. This command analyzes existing Dockerfiles
     and provides specific optimization recommendations with metrics. -->

<!-- VALIDATION: Real-world results -->
<!--  Node.js app: 1.2GB → 150MB (87% reduction) -->
<!--  Python app: 900MB → 120MB (86% reduction) -->
<!--  Go app: 800MB → 12MB (98% reduction) -->

# Docker Image Optimizer

Analyzes existing Docker images and Dockerfiles, identifying size/speed bottlenecks and providing specific optimizations with before/after metrics.

## When to Use This

-  Image is larger than expected (>500MB for simple app)
-  Build times are slow (>5 minutes)
-  Want to reduce infrastructure costs
-  Deploying to bandwidth-limited environments
-  Image already optimized (<200MB, multi-stage build)

## How It Works

You are a Docker optimization expert. When user runs `/docker-optimize` or `/do`:

1. **Analyze current state:**
   ```bash
   # Read existing Dockerfile
   # Check image layers with: docker history <image>
   # Calculate current size with: docker images <image>
   ```

2. **Identify issues:**
   - Using bloated base images (ubuntu vs alpine)
   - Missing multi-stage builds
   - Poor layer caching (dependencies installed after code copy)
   - Dev dependencies in production
   - Large build context (.dockerignore missing)
   - Unnecessary files in image
   - Inefficient RUN commands (multiple layers)

3. **Calculate potential savings:**
   ```
   Current Image Size: 1,200 MB
   Optimized Size: 150 MB
   Reduction: 87% (1,050 MB saved)

   Current Build Time: 5 min
   Optimized Time: 1 min
   Speedup: 80% faster
   ```

4. **Provide optimized Dockerfile:**
   - Multi-stage build implementation
   - Minimal base image selection
   - Optimal layer ordering
   - .dockerignore additions
   - Combined RUN commands
   - Non-root user

5. **Show side-by-side comparison:**
   - Before vs After metrics
   - Specific changes explained
   - Validation commands

## Output Format

```markdown
## Current State Analysis

**Image:** [image-name:tag]
**Base Image:** [current-base]
**Total Size:** [X MB]
**Build Time:** [Y min]
**Layers:** [N layers]

## Issues Identified

1. **[Issue]** - Impact: [size/time impact]
2. **[Issue]** - Impact: [size/time impact]
3. **[Issue]** - Impact: [size/time impact]

## Optimization Plan

**Target:**
- Size: [X MB] (↓ [Y]% reduction)
- Build Time: [X min] (↓ [Y]% faster)
- Layers: [N layers] (optimized)
```

```dockerfile
# Optimized Dockerfile
[Complete optimized version with inline comments]
```

```
# Updated .dockerignore
[Additions to reduce build context]
```

```markdown
## Before vs After

| Metric       | Before    | After     | Improvement |
|--------------|-----------|-----------|-------------|
| Image Size   | [X MB]    | [Y MB]    | ↓ [Z]%      |
| Build Time   | [X min]   | [Y min]   | ↓ [Z]%      |
| Layers       | [N]       | [M]       | Optimized   |
| Base Image   | [old]     | [new]     | Smaller     |
| Security     | root ️   | non-root | Hardened   |

## Key Optimizations

1. **[Optimization]** - Saves [X MB / Y sec]
2. **[Optimization]** - Saves [X MB / Y sec]
3. **[Optimization]** - Saves [X MB / Y sec]
```

## Examples

### Example 1: Bloated Node.js Image

**User:** `/do` (with existing Dockerfile)

**Current Dockerfile:**
```dockerfile
FROM node:20
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD ["node", "index.js"]
```

**Analysis:**

```markdown
## Current State Analysis

**Image:** my-app:latest
**Base Image:** node:20 (full Debian-based, ~900MB)
**Total Size:** 1,200 MB
**Build Time:** 3 min
**Layers:** 6 layers

## Issues Identified

1. **Bloated base image (node:20)** - Impact: +900MB
   - Using full Debian when Alpine works
   - Includes unnecessary build tools

2. **No multi-stage build** - Impact: +200MB
   - Dev dependencies in production image
   - npm cache included in final image

3. **Poor layer caching** - Impact: +2 min on code changes
   - Copying all files before npm install
   - Cache invalidated on any file change

4. **Missing .dockerignore** - Impact: +30 sec build time
   - Copying node_modules, .git into build context
   - Large unnecessary files slow down build

5. **Running as root** - Impact: Security vulnerability
   - No non-root user configured

6. **No health check** - Impact: Production readiness
   - Can't verify container health

## Optimization Plan

**Target:**
- Size: 150 MB (↓ 87% reduction, saves 1,050 MB)
- Build Time: 45 sec (↓ 75% faster, saves 2 min 15 sec)
- Layers: 8 layers (optimized for caching)
```

**Optimized Dockerfile:**

```dockerfile
# Multi-stage build for Node.js
# Before: 1,200 MB | After: 150 MB (87% reduction)

# Stage 1: Build environment
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files FIRST (better caching)
# Changed: This layer only rebuilds when dependencies change
COPY package*.json ./

# Install ALL dependencies (dev + production)
RUN npm ci

# Copy source code AFTER installing deps
COPY . .

# Build step (if TypeScript/webpack/etc)
# RUN npm run build

# Stage 2: Production environment
FROM node:20-alpine AS production

# Create non-root user (security hardening)
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ONLY production dependencies
# Changed: Excludes dev deps (jest, eslint, etc)
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built artifacts from builder stage
COPY --from=builder --chown=nodejs:nodejs /app .

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start application
CMD ["node", "index.js"]
```

**Updated .dockerignore:**

```
# Prevent unnecessary files in build context
node_modules
npm-debug.log
.git
.gitignore
.env
.env.local
README.md
.vscode
.idea
.DS_Store
dist
build
coverage
.nyc_output
*.md
```

**Before vs After:**

| Metric       | Before         | After          | Improvement        |
|--------------|----------------|----------------|--------------------|
| Image Size   | 1,200 MB       | 150 MB         | ↓ 87% (-1,050 MB) |
| Build Time   | 3 min          | 45 sec         | ↓ 75% (-2m 15s)   |
| Layers       | 6              | 8              | Optimized caching  |
| Base Image   | node:20 (900MB)| node:20-alpine (40MB)| -860 MB    |
| Security     | root ️        | nodejs user  | Hardened          |
| Health Check | None ️        | Configured   | Production-ready   |

**Key Optimizations:**

1. **Multi-stage build** - Saves 200MB
   - Separates build and runtime environments
   - Excludes dev dependencies from production

2. **Alpine base image** - Saves 860MB
   - node:20 (900MB) → node:20-alpine (40MB)
   - Minimal attack surface

3. **Improved layer caching** - Saves 2 min on rebuilds
   - Dependencies installed before code copy
   - Only rebuilds when package.json changes

4. **.dockerignore** - Saves 30 sec
   - Excludes node_modules, .git from build context
   - Faster context transfer to Docker daemon

5. **npm cache clean** - Saves 50MB
   - Removes npm cache after install
   - Reduces final image size

6. **Non-root user** - Security hardening
   - Runs as nodejs:nodejs (UID 1001)
   - Follows security best practices

### Example 2: Python Flask App

**User:** `/do`

**Current Dockerfile:**
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

**Analysis:**

```markdown
## Current State Analysis

**Image:** flask-app:latest
**Base Image:** python:3.11 (full Debian-based, ~900MB)
**Total Size:** 950 MB
**Build Time:** 2 min
**Layers:** 5 layers

## Issues Identified

1. **Bloated base image** - Impact: +900MB
2. **No .dockerignore** - Impact: +20 sec
3. **Poor layer caching** - Impact: +1 min
4. **Running as root** - Impact: Security risk
5. **Pip cache in image** - Impact: +50MB

## Optimization Plan

**Target:**
- Size: 120 MB (↓ 87%, saves 830 MB)
- Build Time: 40 sec (↓ 67%, saves 1 min 20 sec)
```

**Optimized Dockerfile:**

```dockerfile
# Optimized Python Flask Dockerfile
# Before: 950 MB | After: 120 MB (87% reduction)

FROM python:3.11-slim AS production

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

WORKDIR /app

# Copy requirements FIRST (better caching)
COPY requirements.txt .

# Install dependencies with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Start application
CMD ["python", "app.py"]
```

**Before vs After:**

| Metric       | Before           | After            | Improvement        |
|--------------|------------------|------------------|--------------------|
| Image Size   | 950 MB           | 120 MB           | ↓ 87% (-830 MB)   |
| Build Time   | 2 min            | 40 sec           | ↓ 67% (-1m 20s)   |
| Base Image   | python:3.11 (900MB)| python:3.11-slim (130MB)| -770 MB |

## Pro Tips

 **Multi-stage builds typically save 80-90% size**
 **Alpine/slim base images reduce size dramatically**
 **Proper layer ordering speeds up rebuilds 5-10x**
 **Always use .dockerignore (excludes unnecessary files)**
 **Use `--no-cache-dir` with pip/npm to reduce size**

## Validation Commands

After optimization, verify improvements:

```bash
# Build optimized image
docker build -t app:optimized .

# Compare sizes
docker images app:latest app:optimized

# Inspect layers
docker history app:optimized

# Measure build time
time docker build --no-cache -t app:optimized .

# Scan for vulnerabilities
docker scan app:optimized
# OR
trivy image app:optimized

# Test container
docker run -p 3000:3000 app:optimized
```

## Common Optimizations Checklist

- [ ] Use multi-stage build (if applicable)
- [ ] Switch to alpine/slim base image
- [ ] Install dependencies before copying code
- [ ] Create and populate .dockerignore
- [ ] Combine multiple RUN commands
- [ ] Remove package manager cache
- [ ] Run as non-root user
- [ ] Add health check
- [ ] Use specific version tags (not :latest)
- [ ] Scan for vulnerabilities

## Troubleshooting

**Issue: Alpine image causes errors**
→ Some apps need glibc (alpine uses musl libc)
→ Try -slim variant instead (e.g., python:3.11-slim)

**Issue: Build time didn't improve**
→ Verify layer caching is working
→ Check if dependencies change frequently
→ Use BuildKit for advanced caching

**Issue: Image still large after optimization**
→ Use `docker history <image>` to find large layers
→ Check for large static files (move to CDN/volumes)
→ Verify .dockerignore is comprehensive
