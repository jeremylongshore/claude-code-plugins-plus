---
name: Managing Network Policies
description: |
  This skill enables Claude to manage Kubernetes network policies and firewall rules. It allows Claude to generate configurations and setup code based on specific requirements and infrastructure. Use this skill when the user requests to create, modify, or analyze network policies for Kubernetes, or when the user mentions "network-policy", "firewall rules", or "Kubernetes security". This skill is useful for implementing best practices and production-ready configurations for network security in a Kubernetes environment.
---

## Overview

This skill empowers Claude to assist with Kubernetes network policy management. It simplifies the creation, modification, and analysis of network policies and firewall rules, ensuring secure and compliant network configurations within Kubernetes clusters.

## How It Works

1. **Receiving User Request**: Claude receives a user request related to Kubernetes network policies or firewall rules.
2. **Invoking network-policy-manager**: Claude invokes the `network-policy-manager` plugin.
3. **Generating Configuration**: The plugin generates the necessary configuration files based on the user's requirements and infrastructure details.

## When to Use This Skill

This skill activates when you need to:
- Create new Kubernetes network policies.
- Modify existing network policies.
- Analyze the impact of network policies on Kubernetes cluster security.

## Examples

### Example 1: Creating a New Network Policy

User request: "Create a network policy that allows pods with the label app=frontend to access pods with the label app=backend on port 8080."

The skill will:
1. Invoke the `network-policy-manager` plugin.
2. Generate a Kubernetes network policy YAML file that implements the requested access control.

### Example 2: Modifying an Existing Network Policy

User request: "Modify the existing network policy 'allow-frontend-to-backend' to also allow access on port 8081."

The skill will:
1. Invoke the `network-policy-manager` plugin.
2. Generate a modified Kubernetes network policy YAML file with the updated port configuration.

## Best Practices

- **Security First**: Always prioritize the principle of least privilege when defining network policies.
- **Regular Audits**: Regularly review and update network policies to adapt to evolving security needs.
- **Testing**: Thoroughly test network policies in a non-production environment before deploying them to production.

## Integration

This skill integrates with other DevOps tools and plugins by generating standard Kubernetes YAML files, which can be applied using `kubectl` or integrated into CI/CD pipelines.