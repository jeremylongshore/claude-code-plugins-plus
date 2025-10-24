---
name: configuring-service-meshes
description: |
  This skill configures service meshes like Istio and Linkerd for microservices. It generates production-ready configurations, implements best practices, and ensures a security-first approach. Use this skill when the user asks to "configure service mesh", "setup Istio", "setup Linkerd", or requests assistance with "service mesh configuration" for their microservices architecture. The configurations will be tailored to the specified infrastructure requirements.
---

## Overview

This skill enables Claude to generate configurations and setup code for service meshes like Istio and Linkerd. It simplifies the process of deploying and managing microservices by automating the configuration of essential service mesh components.

## How It Works

1. **Requirement Gathering**: Claude identifies the specific service mesh (Istio or Linkerd) and infrastructure requirements from the user's request.
2. **Configuration Generation**: Based on the requirements, Claude generates the necessary configuration files, including YAML manifests and setup scripts.
3. **Code Delivery**: Claude provides the generated configurations and setup code to the user, ready for deployment.

## When to Use This Skill

This skill activates when you need to:
- Configure Istio for a microservices application.
- Configure Linkerd for a microservices application.
- Generate service mesh configurations based on specific infrastructure requirements.

## Examples

### Example 1: Setting up Istio

User request: "Configure Istio for my Kubernetes microservices deployment with mTLS enabled."

The skill will:
1. Generate Istio configuration files with mTLS enabled.
2. Provide the generated YAML manifests and setup instructions.

### Example 2: Configuring Linkerd

User request: "Setup Linkerd on my existing microservices cluster, focusing on traffic splitting and observability."

The skill will:
1. Generate Linkerd configuration files for traffic splitting and observability.
2. Provide the generated YAML manifests and setup instructions.

## Best Practices

- **Security**: Always prioritize security configurations, such as mTLS, when configuring service meshes.
- **Observability**: Ensure that the service mesh is configured for comprehensive observability, including metrics, tracing, and logging.
- **Traffic Management**: Use traffic management features like traffic splitting and canary deployments to manage application updates safely.

## Integration

This skill can be integrated with other DevOps tools and plugins in the Claude Code ecosystem to automate the deployment and management of microservices applications. For example, it can work with a Kubernetes deployment plugin to automatically deploy the generated configurations.