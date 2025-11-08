---
name: building-cicd-pipelines
description: |
  This skill enables Claude to generate CI/CD pipeline configurations for various platforms, including GitHub Actions, GitLab CI, and Jenkins. It is used when a user requests the creation of a CI/CD pipeline, specifies a platform (e.g., "GitHub Actions"), or mentions specific pipeline stages like "test," "build," "security," or "deploy." This skill is also useful when the user needs to automate software delivery, integrate security scanning, or set up multi-environment deployments. The skill is triggered by terms such as "CI/CD pipeline," "GitHub Actions pipeline," "GitLab CI configuration," or "Jenkins pipeline."
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to build production-ready CI/CD pipelines, automating software development workflows. It supports multiple platforms and incorporates best practices for testing, building, security, and deployment.

## How It Works

1. **Receiving User Request**: Claude receives a request for a CI/CD pipeline, including the target platform and desired stages.
2. **Generating Configuration**: Claude generates the CI/CD pipeline configuration file (e.g., YAML for GitHub Actions or GitLab CI, Groovy for Jenkins).
3. **Presenting Configuration**: Claude presents the generated configuration to the user for review and deployment.

## When to Use This Skill

This skill activates when you need to:
- Create a CI/CD pipeline for a software project.
- Generate a CI/CD configuration file for GitHub Actions, GitLab CI, or Jenkins.
- Automate testing, building, security scanning, and deployment processes.

## Examples

### Example 1: Creating a GitHub Actions Pipeline

User request: "Create a GitHub Actions pipeline with test, build, and deploy stages."

The skill will:
1. Generate a `github-actions.yml` file with defined test, build, and deploy stages.
2. Present the generated YAML configuration to the user.

### Example 2: Generating a GitLab CI Configuration

User request: "Generate a GitLab CI configuration that includes security scanning."

The skill will:
1. Generate a `.gitlab-ci.yml` file with test, build, security, and deploy stages, including vulnerability scanning.
2. Present the generated YAML configuration to the user.

## Best Practices

- **Security**: Integrate static and dynamic analysis tools into the pipeline to identify vulnerabilities early.
- **Testing**: Include unit, integration, and end-to-end tests to ensure code quality.
- **Deployment**: Use infrastructure-as-code tools to automate infrastructure provisioning and deployment.

## Integration

This skill can be used in conjunction with other plugins to automate infrastructure provisioning, security scanning, and deployment processes. For example, it can work with a cloud deployment plugin to automatically deploy applications to AWS, Azure, or GCP after the CI/CD pipeline successfully builds and tests the code.