# Directory Structure

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
