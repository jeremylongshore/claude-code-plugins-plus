---
name: generating-helm-charts
description: |
  Execute use when generating Helm charts for Kubernetes applications. Trigger with phrases like "create Helm chart", "generate chart for app", "package Kubernetes deployment", or "helm template". Produces production-ready charts with Chart.yaml, values.yaml, templates, and best practices for multi-environment deployments.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(helm:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Generating Helm Charts

## Overview

Generate production-ready Helm 3 charts for Kubernetes applications with Chart.yaml, values.yaml, Go templates, and helper functions. Support multi-environment deployments with values overrides, dependency management, security contexts, health probes, and resource limits following Helm best practices.

## Prerequisites

- Helm 3.x installed (`helm version`)
- `kubectl` configured with cluster access for testing chart installation
- Container images available in a registry accessible from the cluster
- Understanding of application resource requirements (CPU, memory, ports, volumes)
- Chart repository access if publishing (ChartMuseum, OCI registry, or GitHub Pages)

## Instructions

1. Analyze the application: identify container images, ports, environment variables, volumes, and dependencies
2. Scaffold the chart structure: `Chart.yaml`, `values.yaml`, `templates/`, `charts/`, `.helmignore`
3. Create `Chart.yaml` with `apiVersion: v2`, name, version, appVersion, and dependency declarations
4. Define `values.yaml` with sensible production defaults: replica count, image config, resource limits, ingress settings
5. Build templates using Go template syntax with proper `.Values` references and `_helpers.tpl` for reusable named templates
6. Add health checks: `livenessProbe` and `readinessProbe` in the deployment template with configurable paths and thresholds
7. Configure security context: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and drop all capabilities
8. Create environment-specific values files: `values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`
9. Add `NOTES.txt` with post-install instructions showing how to access the application
10. Validate with `helm lint .` and test rendering with `helm template . --values values-prod.yaml`

## Output

- Complete Helm chart directory structure
- `Chart.yaml` with metadata and dependencies
- `values.yaml` with documented, configurable defaults
- Template files: `deployment.yaml`, `service.yaml`, `ingress.yaml`, `configmap.yaml`, `serviceaccount.yaml`, `hpa.yaml`
- `_helpers.tpl` with name, label, and selector helper templates
- `NOTES.txt` with post-install access instructions
- Environment-specific values override files

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Chart.yaml: version is required` | Missing or malformed `version` field | Add a valid SemVer version string to Chart.yaml |
| `parse error in template` | Go template syntax error (missing `end`, wrong function) | Run `helm template .` to pinpoint the error; check bracket matching and function names |
| `dependency not found` | Chart dependency not downloaded | Run `helm dependency update` to fetch dependencies into `charts/` |
| `release failed: timed out waiting for condition` | Pods not reaching ready state during install | Check pod logs; verify image exists, resource limits are sufficient, and probes are correct |
| `values override not applied` | Wrong values file path or key mismatch | Verify `--values` file path and that keys match the structure in `values.yaml` exactly |

## Examples

- "Generate a Helm chart for a Node.js API with 3 replicas, an Nginx ingress, PostgreSQL subchart dependency, and environment-specific values for dev and prod."
- "Create a Helm chart for a stateful application with PersistentVolumeClaim, headless service, and configurable storage class."
- "Package an existing set of Kubernetes manifests into a Helm chart with parameterized image tag, replica count, and resource limits."

## Resources

- Helm documentation: https://helm.sh/docs/
- Chart best practices: https://helm.sh/docs/chart_best_practices/
- Template function reference: https://helm.sh/docs/chart_template_guide/function_list/
- Artifact Hub (chart discovery): https://artifacthub.io/