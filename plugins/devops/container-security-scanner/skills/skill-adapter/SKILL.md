---
name: scanning-container-security
description: |
  This skill enables Claude to scan container images and running containers for vulnerabilities using tools like Trivy and Snyk. It identifies potential security risks in container environments. Use this skill when the user requests a security assessment of a container image, asks to identify vulnerabilities in a container, or wants to improve the security posture of their containerized applications. Trigger terms include "scan container," "container security," "vulnerability assessment," "Trivy scan," or "Snyk scan."
---

## Overview

This skill empowers Claude to perform comprehensive security scans of container images and running containers. By leveraging industry-standard tools, it identifies vulnerabilities and provides insights for remediation, enhancing the overall security of containerized applications.

## How It Works

1. **Receiving Request**: Claude receives a user request to scan a container for vulnerabilities.
2. **Executing Scan**: Claude utilizes tools like Trivy or Snyk to perform the security scan on the specified container image or running container.
3. **Reporting Results**: Claude presents a detailed report of identified vulnerabilities, including severity levels and potential remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Assess the security of a container image before deployment.
- Identify vulnerabilities in a running container within a production environment.
- Generate a security report for compliance purposes.

## Examples

### Example 1: Pre-Deployment Security Check

User request: "Scan this Docker image for vulnerabilities before I deploy it: myapp:latest"

The skill will:
1. Initiate a Trivy scan on the `myapp:latest` Docker image.
2. Return a report listing all identified vulnerabilities, their severity, and suggested fixes.

### Example 2: Runtime Container Security Assessment

User request: "Scan the running container with ID abc123xyz for security vulnerabilities."

The skill will:
1. Execute a Snyk scan on the container with ID `abc123xyz`.
2. Provide a report detailing any vulnerabilities found in the running container, along with remediation advice.

## Best Practices

- **Specify Image Name**: Always provide the full image name (including tag) for accurate scanning.
- **Review Severity Levels**: Pay close attention to high and critical severity vulnerabilities and address them promptly.
- **Regular Scanning**: Schedule regular container security scans to detect new vulnerabilities as they are discovered.

## Integration

This skill can be integrated with other CI/CD pipeline tools to automate security checks as part of the deployment process. It also provides data that can be used with reporting and dashboarding tools to visualize security posture over time.