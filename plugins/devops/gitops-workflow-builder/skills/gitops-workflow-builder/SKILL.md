---
name: building-gitops-workflows
description: |
  This skill enables Claude to construct GitOps workflows using ArgoCD and Flux. It is designed to generate production-ready configurations, implement best practices, and ensure a security-first approach for Kubernetes deployments. Use this skill when the user explicitly requests "GitOps workflow", "ArgoCD", "Flux", or asks for help with setting up a continuous delivery pipeline using GitOps principles. The skill will generate the necessary configuration files and setup code based on the user's specific requirements and infrastructure.
---

## Overview

This skill empowers Claude to create GitOps workflows, automating application deployments and infrastructure management through Git repositories. It provides production-ready configurations for both ArgoCD and Flux, ensuring best practices and a secure approach.

## How It Works

1. **Requirement Gathering**: Claude analyzes the user's request to understand the desired GitOps setup, including the choice of ArgoCD or Flux, target Kubernetes cluster, and application requirements.
2. **Configuration Generation**: Based on the gathered requirements, Claude generates the necessary configuration files, such as ArgoCD Application manifests or Flux Kustomization files.
3. **Code Snippet Creation**: Claude creates code snippets for setting up the GitOps repository structure and deploying the initial configurations to the Kubernetes cluster.

## When to Use This Skill

This skill activates when you need to:
- Create a new GitOps workflow using ArgoCD or Flux.
- Automate application deployments to a Kubernetes cluster using GitOps principles.
- Generate production-ready configurations for GitOps deployments.

## Examples

### Example 1: Setting up ArgoCD for a new application

User request: "Create an ArgoCD workflow to deploy a new application from a Git repository to my Kubernetes cluster."

The skill will:
1. Generate an ArgoCD Application manifest that points to the application's Git repository.
2. Provide instructions on how to deploy the ArgoCD Application to the Kubernetes cluster.

### Example 2: Configuring FluxCD for infrastructure management

User request: "Set up FluxCD to manage my Kubernetes infrastructure configurations stored in a Git repository."

The skill will:
1. Generate Flux Kustomization files that define the desired state of the Kubernetes infrastructure.
2. Provide instructions on how to install FluxCD and configure it to synchronize with the Git repository.

## Best Practices

- **Repository Structure**: Organize your GitOps repository with clear separation of concerns, such as environments (dev, staging, prod) and application components.
- **Declarative Configuration**: Define all application and infrastructure configurations declaratively in Git, using tools like Kustomize or Helm.
- **Automated Reconciliation**: Ensure that your GitOps tool continuously reconciles the desired state in Git with the actual state in the Kubernetes cluster.

## Integration

This skill can be used in conjunction with other skills that manage Kubernetes resources, such as creating deployments, services, and ingress controllers. It also integrates with version control systems like Git to store and manage the GitOps configurations.