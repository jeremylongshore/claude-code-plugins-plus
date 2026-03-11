---
name: generating-docker-compose-files
description: |
  Execute use when you need to work with Docker Compose.
  This skill provides Docker Compose file generation with comprehensive guidance and automation.
  Trigger with phrases like "generate docker-compose", "create compose file",
  or "configure multi-container app".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Generating Docker Compose Files

## Overview

Generate production-ready `docker-compose.yml` files for multi-container applications. Define services, networks, volumes, health checks, resource limits, and environment-specific overrides for local development, testing, and single-host production deployments.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose v2 (`docker compose version`)
- Application Dockerfiles for each service or pre-built images available
- Understanding of service dependencies and inter-service communication ports
- Environment variable values or `.env` files for configuration
- Sufficient disk space and memory for all containers defined in the stack

## Instructions

1. Scan the project for existing Dockerfiles, `docker-compose*.yml` files, and application entry points
2. Identify all services that compose the application stack (web server, API, database, cache, message queue, worker)
3. Define each service with image or build context, port mappings, and environment variables
4. Configure service dependencies using `depends_on` with health check conditions to ensure proper startup order
5. Create named volumes for persistent data (database files, uploads, cache) and bind mounts for development hot-reload
6. Define custom bridge networks to isolate service groups (frontend, backend, data tier)
7. Add health checks for each service to enable dependency-aware startup and container orchestrator integration
8. Set resource limits (`deploy.resources.limits`) for CPU and memory to prevent a single container from exhausting the host
9. Create environment-specific override files: `docker-compose.override.yml` for development, `docker-compose.prod.yml` for production
10. Validate the configuration with `docker compose config` to check for syntax errors

## Output

- `docker-compose.yml` with service definitions, networks, and volumes
- Environment-specific override files (`docker-compose.override.yml`, `docker-compose.prod.yml`)
- `.env` file template with documented variables
- Dockerfiles for services that require custom builds
- Helper scripts for common operations (`start.sh`, `stop.sh`, `logs.sh`)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `port is already allocated` | Another container or host process using the same port | Change the host port mapping or stop the conflicting process |
| `network not found` | Referenced network not defined in the compose file | Add the network under the top-level `networks:` key |
| `service depends on undefined service` | Typo in `depends_on` or missing service definition | Verify service names match exactly between `depends_on` and service definitions |
| `volume mount permission denied` | Host directory owned by different user than container process | Use `user:` directive in service or set proper ownership with an init script |
| `OOM killed` | Container exceeded memory limit | Increase `deploy.resources.limits.memory` or optimize application memory usage |

## Examples

- "Generate a docker-compose.yml for a Node.js API + PostgreSQL + Redis stack with health checks, named volumes, and a development override with hot-reload."
- "Create a compose file for a WordPress site with MySQL, Nginx reverse proxy, and Certbot for automatic SSL certificate renewal."
- "Build a docker-compose stack for a microservices app with 3 APIs, RabbitMQ message broker, and a shared Postgres database with isolated networks."

## Resources

- Docker Compose specification: https://docs.docker.com/compose/compose-file/
- Docker Compose best practices: https://docs.docker.com/compose/production/
- Compose file versioning: https://docs.docker.com/compose/compose-file/compose-versioning/
- Multi-environment guide: https://docs.docker.com/compose/extends/