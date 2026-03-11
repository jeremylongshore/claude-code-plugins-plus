---
name: scanning-container-security
description: |
  Execute use when you need to work with security and compliance.
  This skill provides security scanning and vulnerability detection with comprehensive guidance and automation.
  Trigger with phrases like "scan for vulnerabilities", "implement security controls",
  or "audit security".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Scanning Container Security

## Overview

Scan container images and Dockerfiles for vulnerabilities, misconfigurations, and compliance violations using Trivy, Grype, Snyk Container, and Hadolint. Analyze base images, OS packages, application dependencies, and runtime configurations to produce actionable security reports with remediation guidance.

## Prerequisites

- Container scanning tool installed: `trivy`, `grype`, `snyk`, or `docker scout`
- Dockerfile linter: `hadolint` for Dockerfile best practice validation
- Docker daemon running for local image scanning
- Access to the container images to scan (local, registry, or tar archive)
- `jq` for parsing JSON scan results

## Instructions

1. Identify target images for scanning: production images, base images, and CI-built images
2. Lint Dockerfiles with `hadolint Dockerfile` to catch misconfigurations before build (privileged instructions, pinned versions, shell best practices)
3. Scan built images for OS-level vulnerabilities: `trivy image <image:tag>` or `grype <image:tag>`
4. Scan for application dependency vulnerabilities: check language-specific packages (npm, pip, Maven, Go modules) embedded in the image
5. Check for secrets accidentally baked into image layers: `trivy image --scanners secret <image:tag>`
6. Evaluate image against CIS Docker Benchmark: verify non-root user, read-only filesystem capability, health checks defined
7. Generate a security report with severity classification (Critical, High, Medium, Low) and CVE identifiers
8. Produce remediation steps: upgrade base image, pin package versions, replace vulnerable dependencies
9. Integrate scanning into CI/CD pipeline: fail builds on Critical/High vulnerabilities, generate SARIF output for GitHub Security tab

## Output

- Vulnerability scan report in JSON, table, or SARIF format
- Hadolint report with Dockerfile improvement recommendations
- Remediation Dockerfile patches (updated base image, pinned package versions)
- CI/CD pipeline step configuration for automated image scanning
- Security policy document defining acceptable risk thresholds

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `trivy: unable to pull image` | Image not found locally or registry auth failure | Pull image first with `docker pull` or configure registry credentials |
| `CRITICAL vulnerability found but no fix available` | Upstream package has no patch yet | Document as accepted risk, use `--ignore-unfixed` flag, or switch to an alternative base image |
| `hadolint: DL3008 pin versions in apt-get install` | Packages installed without version pinning | Add version pins (e.g., `apt-get install nginx=1.24.0-1`) or use `--no-install-recommends` |
| `Scan timeout on large image` | Image has many layers or large filesystem | Use `--timeout 15m` flag; scan a specific layer or use `--skip-dirs` to exclude test data |
| `False positive CVE` | Scanner database maps CVE to a package not actually exploitable | Add to `.trivyignore` or Grype ignore file with justification comment |

## Examples

- "Scan all production Docker images for Critical and High CVEs, generate a report, and create Jira tickets for each finding."
- "Lint the Dockerfile for best practices: ensure multi-stage build, non-root USER, no ADD for remote URLs, and pinned base image digest."
- "Set up a GitHub Actions step that runs Trivy on every PR, fails on Critical vulnerabilities, and uploads results to the Security tab via SARIF."

## Resources

- Trivy: https://aquasecurity.github.io/trivy/
- Grype: https://github.com/anchore/grype
- Hadolint: https://github.com/hadolint/hadolint
- Docker Scout: https://docs.docker.com/scout/
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
