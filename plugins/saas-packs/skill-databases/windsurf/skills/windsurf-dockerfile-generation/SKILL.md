---
name: windsurf-dockerfile-generation
description: |
  Create optimized Dockerfiles with AI-driven best practices. Activate when users mention
  "create dockerfile", "container image", "docker optimization", "containerize application",
  or "docker best practices". Handles Docker configuration generation.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Dockerfile Generation

Create optimized Dockerfiles with AI-driven best practices.

## Directory Structure

```
project-root/
    Dockerfile                       # Production Dockerfile
        # Multi-stage build
        # Minimal base image
        # Security hardening
        # Layer optimization

    Dockerfile.dev                   # Development Dockerfile
        # Development tools included
        # Hot reload support
        # Debugging capabilities

    docker-compose.yml               # Service orchestration
        # Service definitions
        # Network configuration
        # Volume mappings

    docker-compose.dev.yml           # Development overrides
        # Source mounting
        # Port exposures
        # Dev tool containers

    .dockerignore                    # Build context exclusions
        # Node modules
        # Build artifacts
        # Local configuration

    .windsurf/
        docker/
            templates/
                node-app.dockerfile      # Node.js template
                    # Optimal base image selection
                    # Dependency layer caching
                    # Non-root user setup

                python-app.dockerfile    # Python template
                    # Virtual environment
                    # Requirements optimization
                    # Health check patterns

            security-scan.json           # Security checklist
                # Base image vulnerabilities
                # Secret exposure risks
                # Permission issues
```

## Best Practices

### Layer Optimization
- Order commands by change frequency
- Combine RUN statements
- Use .dockerignore effectively
- Leverage build cache

### Security
- Use minimal base images
- Run as non-root user
- Scan for vulnerabilities
- No secrets in images

## Configuration Steps

1. **Analyze Application**
   - Identify dependencies
   - Map build process
   - Document runtime needs

2. **Generate Dockerfile**
   - Use Cascade for initial generation
   - Apply best practices
   - Optimize for size

3. **Validate and Test**
   - Build and run locally
   - Check image size
   - Run security scans

## Success Criteria

- Successful build on first attempt
- Minimal image size
- Security best practices applied
- 70% reduction in build failures
