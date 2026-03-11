---
name: managing-environment-configurations
description: |
  Implement environment and configuration management with comprehensive guidance and automation.
  Use when you need to work with environment configuration.
  Trigger with phrases like "manage environments", "configure environments",
  or "sync configurations".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Managing Environment Configurations

## Overview

Manage application configurations across development, staging, and production environments using `.env` files, Kubernetes ConfigMaps/Secrets, SSM Parameter Store, and cloud-native configuration services. Enforce consistency, prevent configuration drift, and implement safe promotion workflows between environments.

## Prerequisites

- Access to all target environments (dev, staging, production)
- Configuration management tool or pattern identified (dotenv, ConfigMaps, SSM, Consul)
- Version control for configuration files (separate repo or encrypted in application repo)
- Encryption tool for sensitive values (`sops`, `age`, `sealed-secrets`, or cloud KMS)
- Understanding of which values differ between environments vs. which are shared

## Instructions

1. Audit existing configuration: scan for `.env` files, `config/` directories, Kubernetes ConfigMaps, and hardcoded values in source code
2. Classify each configuration value: public (non-sensitive, varies per env), secret (credentials, API keys), and static (same across all envs)
3. Extract hardcoded values into externalized configuration with a clear naming convention (`APP_DATABASE_HOST`, `APP_REDIS_URL`)
4. Create environment-specific configuration files: `.env.development`, `.env.staging`, `.env.production`
5. Encrypt sensitive values using `sops` with cloud KMS or `sealed-secrets` for Kubernetes
6. Generate Kubernetes ConfigMaps and Secrets from environment files for cluster-based deployments
7. Set up configuration validation: schema checks to ensure all required variables are present before deployment
8. Implement promotion workflow: changes go to dev first, then promote to staging after testing, then to production with approval
9. Add configuration drift detection: compare running environment against source-of-truth on a schedule

## Output

- Environment-specific configuration files (`.env.*`, `config/*.yaml`)
- Kubernetes ConfigMap and Secret manifests per environment
- Configuration schema/validation script to catch missing variables
- SOPS-encrypted secret files with `.sops.yaml` rules
- CI/CD pipeline steps for configuration validation and deployment

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Missing required environment variable` | Variable defined in schema but absent from `.env` file | Add the variable to the environment file; run validation script before deploy |
| `SOPS decryption failed` | Wrong KMS key or expired credentials | Verify KMS key ARN in `.sops.yaml`; refresh cloud credentials |
| `ConfigMap too large` | Kubernetes 1MB ConfigMap size limit exceeded | Split into multiple ConfigMaps or mount as files from a volume |
| `Configuration drift detected` | Manual changes made directly to running environment | Re-apply configuration from source-of-truth; block direct environment edits |
| `Secret exposed in logs` | Application logging sensitive config values at startup | Mask secrets in logging output; audit code for accidental secret printing |

## Examples

- "Create an environment configuration system using `.env` files for a Node.js app with SOPS encryption for secrets and validation that all required vars are set."
- "Generate Kubernetes ConfigMaps and Secrets from environment files for dev, staging, and production namespaces."
- "Set up a configuration promotion workflow: edit in dev, validate in CI, promote to staging via PR, deploy to production with approval gate."

## Resources

- 12-Factor App config: https://12factor.net/config
- SOPS encryption: https://github.com/getsops/sops
- Kubernetes ConfigMaps: https://kubernetes.io/docs/concepts/configuration/configmap/
- Sealed Secrets: https://github.com/bitnami-labs/sealed-secrets
- Consul KV: https://developer.hashicorp.com/consul/docs/dynamic-app-config/kv
