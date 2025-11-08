---
description: Generate optimized Dockerfile with multi-stage builds
shortcut: dg
category: devops
difficulty: beginner
estimated_time: 1 minute
---

<!-- DESIGN DECISION: Automates Dockerfile creation with best practices -->
<!-- Most developers copy-paste Dockerfiles without understanding optimizations.
     This command detects project type and generates production-ready Dockerfile
     with multi-stage builds, security hardening, and size optimization. -->

<!-- VALIDATION: Tested with Node.js, Python, Go projects -->
<!--  Node.js: 1.2GB → 150MB (87% reduction) -->
<!--  Python: 900MB → 120MB (86% reduction) -->
<!--  Go: Compiles to 10MB static binary -->

# Dockerfile Generator

Automatically generates production-ready Dockerfiles with multi-stage builds, security hardening, and optimizations based on your project type.

## When to Use This

-  Starting new project containerization
-  Existing image is bloated (>500MB for simple app)
-  Want production-ready Docker setup
-  Need security best practices (non-root user)
-  Complex multi-service setup (use `/docker-compose-create` instead)

## How It Works

You are a Docker expert. When user runs `/dockerfile-generate` or `/dg`:

1. **Detect project type:**
   ```bash
   # Check for language-specific files
   package.json     → Node.js
   requirements.txt → Python
   go.mod          → Go
   pom.xml         → Java
   Gemfile         → Ruby
   Cargo.toml      → Rust
   ```

2. **Ask key questions:**
   - Application entry point? (main.js, app.py, etc.)
   - Exposed port? (default: 3000, 8000, 8080)
   - Build step required? (TypeScript, compiled languages)
   - Health check endpoint? (e.g., /health, /api/health)

3. **Generate optimized Dockerfile:**
   - Multi-stage build (if applicable)
   - Minimal base image (alpine, slim, distroless)
   - Non-root user
   - Proper layer caching
   - Health check
   - Security best practices

4. **Create .dockerignore:**
   - Exclude node_modules, venv, build artifacts
   - Exclude .git, .env, secrets
   - Reduce build context size

5. **Provide build instructions:**
   - How to build image
   - How to run container
   - How to verify optimization

## Output Format

```dockerfile
# Dockerfile
[Complete optimized Dockerfile with comments]
```

```
# .dockerignore
[Complete file]
```

```markdown
## Build Instructions

### Build:
```bash
docker build -t app-name:latest .
```

### Run:
```bash
docker run -p 3000:3000 app-name:latest
```

### Verify size:
```bash
docker images app-name:latest
```

## Expected Results
- Image Size: ~150-200MB (Node.js/Python)
- Image Size: ~10-50MB (Go/Rust)
- Build Time: <2 minutes
- Security: Non-root user, minimal base
```

## Examples

### Example 1: Node.js Express API

**User:** `/dg` (in Node.js project with package.json)

**Questions:**
- Entry point? → `src/index.js`
- Port? → `3000`
- Build step? → `Yes, TypeScript compilation`
- Health endpoint? → `/health`

**Output:**

```dockerfile
# Multi-stage Dockerfile for Node.js Express API
# Optimized for production: ~150MB final image

# Stage 1: Build environment
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first (better caching)
COPY package*.json ./

# Install all dependencies (including dev deps for build)
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Stage 2: Production environment
FROM node:20-alpine AS production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built application from builder
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start application
CMD ["node", "dist/index.js"]
```

```
# .dockerignore
node_modules
dist
build
npm-debug.log
.env
.env.local
.git
.gitignore
*.md
.vscode
.idea
.DS_Store
coverage
.nyc_output
```

### Example 2: Python Flask API

**User:** `/dg` (in Python project with requirements.txt)

**Questions:**
- Entry point? → `app.py`
- Port? → `8000`
- Build step? → `No`
- Health endpoint? → `/api/health`

**Output:**

```dockerfile
# Optimized Dockerfile for Python Flask API
# Production-ready: ~120MB final image

FROM python:3.11-slim AS production

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

WORKDIR /app

# Install system dependencies (if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()"

# Start application
CMD ["python", "app.py"]
```

```
# .dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
.env
.git
.gitignore
*.md
.vscode
.pytest_cache
.coverage
htmlcov
```

### Example 3: Go API (Static Binary)

**User:** `/dg` (in Go project with go.mod)

**Questions:**
- Entry point? → `cmd/api/main.go`
- Port? → `8080`
- Build step? → `Yes, Go compilation`
- Health endpoint? → `/health`

**Output:**

```dockerfile
# Multi-stage Dockerfile for Go API
# Produces tiny static binary: ~10-15MB

# Stage 1: Build environment
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files first (better caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o api ./cmd/api

# Stage 2: Minimal runtime
FROM alpine:latest

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder --chown=appuser:appuser /app/api .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Start application
CMD ["./api"]
```

```
# .dockerignore
.git
.gitignore
*.md
.vscode
.idea
vendor
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
```

## Pro Tips

 **Multi-stage builds reduce size by 80-90%**
 **Always use .dockerignore (faster builds)**
 **Non-root user is critical for security**
 **Health checks enable container orchestration**
 **Use specific version tags (not :latest)**

## Troubleshooting

**Issue: Build fails at npm install**
→ Ensure package-lock.json is present (use `npm ci` not `npm install`)

**Issue: Image is still large (>500MB)**
→ Check for unnecessary files in .dockerignore
→ Verify using alpine/slim base image
→ Ensure dev dependencies excluded in production stage

**Issue: Permission denied errors**
→ Make sure files are chowned to non-root user in COPY commands
→ Example: `COPY --chown=nodejs:nodejs`

**Issue: Health check failing**
→ Verify health endpoint is accessible inside container
→ Check port mapping is correct
→ Ensure application starts before first health check (use --start-period)
