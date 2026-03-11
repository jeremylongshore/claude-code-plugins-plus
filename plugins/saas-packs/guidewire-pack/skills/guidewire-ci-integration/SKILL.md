---
name: guidewire-ci-integration
description: |
  Configure CI/CD pipelines for Guidewire InsuranceSuite development.
  Use when setting up automated builds, tests, and deployments for Guidewire projects.
  Trigger with phrases like "guidewire ci", "guidewire pipeline",
  "automated testing guidewire", "jenkins guidewire", "github actions guidewire".
allowed-tools: Read, Write, Edit, Bash(gradle:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire CI Integration

## Overview

Configure continuous integration and continuous deployment pipelines for Guidewire InsuranceSuite projects using GitHub Actions, Jenkins, or Azure DevOps.

## Prerequisites

- Git repository with Guidewire project
- CI/CD platform access (GitHub Actions, Jenkins, or Azure DevOps)
- Guidewire Cloud Console access for deployment credentials
- JDK 17 and Gradle available in CI environment

## Instructions

### Step 1: GitHub Actions Workflow

Create `.github/workflows/guidewire-ci.yml` with jobs for build, test (with PostgreSQL service), security scan (CodeQL + OWASP), and environment-gated deployments to sandbox and production.

### Step 2: Jenkins Pipeline

Create a `Jenkinsfile` with parallel code quality stages (Gosu check + SpotBugs), test reporting with JUnit and JaCoCo, and manual approval gate for production deployment.

### Step 3: Gradle Build Configuration

Configure `build.gradle` with JaCoCo (70% coverage minimum), OWASP dependency check (fail on CVSS 7.0+), SpotBugs, and a unified `ci` task that runs all checks.

### Step 4: Test Utilities

Create a `CITestBase` class with database health checks, test data cleanup for `TEST-*` prefixed accounts, and conditional slow-test skipping in CI.

### Step 5: Deployment Script

Write `deploy-to-cloud.sh` that authenticates via OAuth2, uploads the configuration package ZIP, and polls deployment status until complete or failed.

For complete workflow files, Jenkinsfile, Gradle config, and deployment scripts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- GitHub Actions workflow file
- Jenkins pipeline configuration
- Gradle build with CI tasks
- Test utilities for CI environment
- Cloud deployment script

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Build timeout | Long-running tests | Increase timeout or parallelize |
| Database connection failed | Service not ready | Add health check wait |
| Deployment failed | Invalid package | Check build artifacts |
| Test flakiness | Race conditions | Add proper test isolation |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Guidewire Gradle Plugin](https://docs.guidewire.com/tools/gradle-plugin/)

## Next Steps

For deployment strategies, see `guidewire-deploy-integration`.

## Examples

**Basic usage**: Apply guidewire ci integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire ci integration for production environments with multiple constraints and team-specific requirements.