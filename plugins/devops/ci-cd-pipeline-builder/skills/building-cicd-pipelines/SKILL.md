---
name: building-cicd-pipelines
description: |
  Execute use when you need to work with deployment and CI/CD.
  This skill provides deployment automation and pipeline orchestration with comprehensive guidance and automation.
  Trigger with phrases like "deploy application", "create pipeline",
  or "automate deployment".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*), Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Building CI/CD Pipelines

## Current State
!`ls .github/workflows/*.yml .gitlab-ci.yml Jenkinsfile .circleci/config.yml 2>/dev/null || echo 'No CI/CD config found'`

## Overview

Generate CI/CD pipeline configurations for GitHub Actions, GitLab CI, Jenkins, CircleCI, and Azure DevOps. Produce multi-stage workflows covering linting, testing, building container images, security scanning, and deploying to staging/production with proper gating and rollback mechanisms.

## Prerequisites

- Git repository hosted on a supported platform (GitHub, GitLab, Bitbucket, Azure DevOps)
- Container runtime (Docker) if building images
- Target deployment environment credentials configured as pipeline secrets
- Test suite that can run headlessly (`npm test`, `pytest`, `go test`, etc.)
- Understanding of branching strategy (trunk-based, GitFlow, or environment branches)

## Instructions

1. Scan the project for existing CI/CD configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`)
2. Identify the application stack: language, framework, test runner, package manager, and deployment target
3. Define pipeline stages: `lint` -> `test` -> `build` -> `security-scan` -> `deploy-staging` -> `integration-test` -> `deploy-production`
4. Generate the pipeline configuration file with appropriate triggers (push to main, PR events, tags)
5. Add caching for dependencies (`node_modules`, `.pip-cache`, Go modules) to reduce build times
6. Configure matrix builds for multiple language versions or OS targets where appropriate
7. Add secret references for deployment credentials, container registry tokens, and API keys (never hardcode)
8. Implement deployment gates: manual approval for production, automated rollback on health check failure
9. Add status badges and notifications (Slack, email) for build results
10. Validate the pipeline syntax using platform-specific tools (`actionlint`, `gitlab-ci-lint`)

## Output

- Pipeline configuration files (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`)
- Dockerfile for container builds (multi-stage, minimal base image)
- Deployment scripts or Kubernetes manifests referenced by the pipeline
- Environment-specific variable files for staging vs. production

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Pipeline triggered but no jobs run` | Trigger conditions (paths, branches) do not match | Review `on:` / `only:` / `rules:` filters and verify branch names |
| `Docker build failed: layer cache miss` | Cache key changed or cache storage expired | Use content-based cache keys (`hashFiles('**/package-lock.json')`) and verify cache backend |
| `Secret not found` | Secret name mismatch or not set in pipeline settings | Check secret names match exactly (case-sensitive) in repository/project settings |
| `Deploy failed: unauthorized` | Expired or incorrect deployment credentials | Rotate credentials, update pipeline secrets, and verify IAM role/service account permissions |
| `Tests pass locally but fail in CI` | Environment differences (OS, node version, timezone) | Pin runtime versions in pipeline config; use `matrix` to test across environments |

## Examples

- "Create a GitHub Actions workflow for a Node.js app: lint with ESLint, test with Jest, build Docker image, push to ECR, deploy to EKS staging on PR merge."
- "Generate a GitLab CI pipeline with parallel test jobs, SAST scanning, and manual production deployment gate."
- "Build a Jenkins pipeline that runs Python tests in a Docker agent, publishes coverage to SonarQube, and deploys via Terraform."

## Resources

- GitHub Actions: https://docs.github.com/en/actions
- GitLab CI/CD: https://docs.gitlab.com/ee/ci/
- Jenkins Pipeline: https://www.jenkins.io/doc/book/pipeline/
- CI/CD best practices: https://martinfowler.com/articles/continuousIntegration.html