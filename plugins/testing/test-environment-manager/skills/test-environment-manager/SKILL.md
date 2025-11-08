---
name: managing-test-environments
description: |
  This skill enables Claude to manage isolated test environments using Docker Compose, Testcontainers, and environment variables. It is used to create consistent, reproducible testing environments for software projects. Claude should use this skill when the user needs to set up a test environment with specific configurations, manage Docker Compose files for test infrastructure, set up programmatic container management with Testcontainers, manage environment variables for tests, or ensure cleanup after tests. Trigger terms include "test environment", "docker compose", "testcontainers", "environment variables", "isolated environment", "env-setup", and "test setup".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to orchestrate and manage isolated test environments, ensuring consistent and reproducible testing processes. It simplifies the setup and teardown of complex testing infrastructures by leveraging Docker Compose, Testcontainers, and environment variable management.

## How It Works

1. **Environment Creation**: Generates isolated test environments with databases, caches, message queues, and other dependencies.
2. **Docker Compose Management**: Creates and configures `docker-compose.yml` files to define the test infrastructure.
3. **Testcontainers Integration**: Sets up programmatic container management using Testcontainers for dynamic environment configuration.

## When to Use This Skill

This skill activates when you need to:
- Create an isolated test environment for a software project.
- Manage Docker Compose files for test infrastructure.
- Set up programmatic container management using Testcontainers.

## Examples

### Example 1: Setting up a Database Test Environment

User request: "Set up a test environment with a PostgreSQL database and a Redis cache using Docker Compose."

The skill will:
1. Generate a `docker-compose.yml` file defining PostgreSQL and Redis services.
2. Configure environment variables for database connection and cache access.

### Example 2: Creating a Test Environment with Message Queue

User request: "Create a test environment with RabbitMQ using Testcontainers."

The skill will:
1. Programmatically create a RabbitMQ container using Testcontainers.
2. Configure environment variables for message queue connection.

## Best Practices

- **Configuration**: Ensure that all necessary environment variables are properly configured for the test environment.
- **Cleanup**: Implement cleanup routines to remove test environments after use.
- **Isolation**: Verify that the test environment is properly isolated from other environments.

## Integration

This skill integrates with other Claude Code plugins to manage the deployment and execution of tests within the created environments. It can work with CI/CD tools to automate testing workflows.