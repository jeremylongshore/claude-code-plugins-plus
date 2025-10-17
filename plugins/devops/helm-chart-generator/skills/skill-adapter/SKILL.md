---
name: Generating Helm Charts
description: |
  This skill enables Claude to generate Helm charts for Kubernetes applications. It should be used when the user requests the creation of a new Helm chart, the modification of an existing chart, or assistance with packaging and deploying Kubernetes applications using Helm. The skill is triggered by requests that mention "Helm chart", "Kubernetes deployment", "package application for Kubernetes", or similar phrases related to Helm and Kubernetes. It helps streamline the process of creating and managing Kubernetes deployments.
---

## Overview

This skill empowers Claude to create and manage Helm charts, simplifying Kubernetes application deployments. It provides production-ready configurations, implements best practices, and supports multi-platform environments.

## How It Works

1. **Receiving Requirements**: Claude receives the user's requirements for the Helm chart, including application details, dependencies, and desired configurations.
2. **Generating Chart**: Claude utilizes the helm-chart-generator plugin to generate a complete Helm chart based on the provided requirements.
3. **Providing Chart**: Claude presents the generated Helm chart to the user, ready for deployment.

## When to Use This Skill

This skill activates when you need to:
- Create a new Helm chart for a Kubernetes application.
- Modify an existing Helm chart to update application configurations.
- Package and deploy an application to Kubernetes using Helm.

## Examples

### Example 1: Creating a Basic Web App Chart

User request: "Create a Helm chart for a simple web application with a single deployment and service."

The skill will:
1. Generate a basic Helm chart including a `Chart.yaml`, `values.yaml`, a deployment, and a service.
2. Provide the generated chart files for review and customization.

### Example 2: Adding Ingress to an Existing Chart

User request: "Modify the existing Helm chart for my web application to include an ingress resource."

The skill will:
1. Update the existing Helm chart to include an ingress resource, configured based on best practices.
2. Provide the updated chart files with the new ingress configuration.

## Best Practices

- **Configuration Management**: Utilize `values.yaml` to manage configurable parameters within the Helm chart.
- **Resource Limits**: Define resource requests and limits for deployments to ensure efficient resource utilization.
- **Security Contexts**: Implement security contexts to enhance the security posture of the deployed application.

## Integration

This skill integrates with other Claude Code skills by providing a standardized way to package and deploy applications to Kubernetes. It can be combined with skills that generate application code, manage infrastructure, or automate deployment pipelines.