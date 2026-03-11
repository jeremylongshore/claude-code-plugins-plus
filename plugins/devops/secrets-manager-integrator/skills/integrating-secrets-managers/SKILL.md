---
name: integrating-secrets-managers
description: |
  Manage this skill enables AI assistant to seamlessly integrate with various secrets managers like hashicorp vault and aws secrets manager. it generates configurations and setup code, ensuring best practices for secure credential management. use this skill when... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Integrating Secrets Managers

## Overview

Integrate secrets management platforms (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault) into applications and infrastructure. Generate authentication configurations, access policies, secret rotation schedules, and application code patterns for secure credential retrieval at runtime.

## Prerequisites

- Secrets manager instance running and accessible (Vault server, AWS Secrets Manager enabled)
- Cloud provider CLI authenticated or Vault CLI installed (`vault`, `aws`, `gcloud`, `az`)
- IAM/policy permissions to create secrets and access policies
- Understanding of which application components need which secrets
- Network connectivity between application workloads and the secrets manager endpoint

## Instructions

1. Inventory all secrets currently in use: database credentials, API keys, TLS certificates, OAuth tokens
2. Select the secrets manager based on infrastructure: Vault for multi-cloud, AWS Secrets Manager for AWS-native, GCP Secret Manager for GCP
3. Create the secrets store structure: organize by application, environment, and secret type (e.g., `apps/myapp/prod/database`)
4. Generate access policies with least-privilege: each application identity gets read access only to its own secrets
5. Configure authentication method: Kubernetes service account (Vault K8s auth), IAM role (AWS), Workload Identity (GCP)
6. Implement secret retrieval in the application: SDK call at startup, sidecar injection (Vault Agent), or CSI driver mount
7. Set up automatic secret rotation: define rotation lambda/function, rotation interval, and notification on rotation events
8. Remove hardcoded secrets from code and configuration files; replace with secret references
9. Add monitoring: alert on secret access failures, rotation failures, and unauthorized access attempts

## Output

- Vault policies (HCL) or IAM policies (JSON) for secret access
- Authentication configuration (Vault K8s auth, AWS IAM role, GCP Workload Identity)
- Application code snippets for secret retrieval (SDK-based or environment variable injection)
- Secret rotation configuration (AWS rotation Lambda, Vault dynamic secrets)
- Kubernetes External Secrets Operator or CSI SecretProviderClass manifests

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `permission denied` on secret read | Policy does not grant access to the requested path | Update Vault policy or IAM policy to include the specific secret ARN/path |
| `Vault token expired` | Authentication token TTL exceeded | Configure token renewal or use short-lived tokens with auto-renewal via Vault Agent |
| `Secret not found` | Secret path/name incorrect or secret deleted | Verify the secret exists with `vault kv get` or `aws secretsmanager describe-secret` |
| `Rotation failed` | Rotation function lacks permissions or target service unreachable | Check rotation function logs; verify it has permissions to update credentials on the target service |
| `Connection refused to Vault` | Vault server down or network policy blocking access | Verify Vault is running and healthy; check network policies/firewalls between application and Vault |

## Examples

- "Integrate HashiCorp Vault with a Kubernetes deployment using the Vault Agent sidecar injector to inject database credentials as environment variables."
- "Set up AWS Secrets Manager with automatic rotation every 30 days for an RDS PostgreSQL password, with a Lambda rotation function."
- "Replace all hardcoded API keys in the application with GCP Secret Manager references using Workload Identity for authentication."

## Resources

- HashiCorp Vault: https://developer.hashicorp.com/vault/docs
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
- GCP Secret Manager: https://cloud.google.com/secret-manager/docs
- External Secrets Operator: https://external-secrets.io/
- Secrets management best practices: https://developer.hashicorp.com/vault/tutorials/recommended-patterns