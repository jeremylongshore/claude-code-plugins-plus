---
name: generating-docker-compose-files
description: |
  This skill enables Claude to generate Docker Compose configurations for multi-container applications. It leverages best practices for production-ready deployments, including defining services, networks, volumes, health checks, and resource limits. Claude should use this skill when the user requests a Docker Compose file, specifies application architecture involving multiple containers, or mentions needs for container orchestration, environment variables, or persistent data management in a Docker environment. Trigger terms include "docker-compose", "docker compose file", "multi-container", "container orchestration", "docker environment", "service definition", "volume management", "network configuration", "health checks", "resource limits", and ".env files".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to create fully functional Docker Compose files, streamlining the deployment of complex applications. It automatically incorporates recommended configurations for service dependencies, data persistence, and resource optimization.

## How It Works

1. **Receiving User Input**: Claude interprets the user's request, identifying the application's architecture and dependencies.
2. **Generating Compose Configuration**: Based on the interpreted request, Claude generates a `docker-compose.yml` file defining services, networks, volumes, and other configurations.
3. **Presenting the Configuration**: Claude provides the generated `docker-compose.yml` file to the user.

## When to Use This Skill

This skill activates when you need to:
- Generate a Docker Compose file for a multi-container application.
- Define service dependencies and network configurations for a Docker environment.
- Manage persistent data using Docker volumes.
- Configure health checks and resource limits for Docker containers.

## Examples

### Example 1: Deploying a Full-Stack Application

User request: "Generate a docker-compose file for a full-stack application with a Node.js frontend, a Python backend, and a PostgreSQL database."

The skill will:
1. Generate a `docker-compose.yml` file defining three services: `frontend`, `backend`, and `database`.
2. Configure network connections between the services and define volumes for persistent database storage.

### Example 2: Adding Health Checks

User request: "Create a docker-compose file for a Redis server with a health check."

The skill will:
1. Generate a `docker-compose.yml` file defining a Redis service.
2. Add a health check configuration to the Redis service, ensuring the container restarts if it becomes unhealthy.

## Best Practices

- **Service Dependencies**: Explicitly define dependencies between services using the `depends_on` directive.
- **Environment Variables**: Utilize `.env` files to manage environment variables and sensitive information.
- **Volume Naming**: Use named volumes for data persistence and avoid relying on host paths.

## Integration

This skill integrates with other development tools by providing a standardized Docker Compose configuration that can be used with Docker CLI, Docker Desktop, and other container management platforms.