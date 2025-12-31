# clay-multi-env-setup

## File Scaffold

```
clay-multi-env-setup/
|-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Configure Clay across development, staging, and production environments. Implements secure configuration management and environment isolation.
**Workflow:** Enterprise setup skill. Use when establishing multi-environment Clay deployments.
**Relates to:** Builds on clay-reference-architecture; enables clay-enterprise-rbac for access control.

## Summary

This skill configures Clay for multi-environment deployments. It covers environment-specific configuration structures, secure secret management with HashiCorp Vault or cloud secret managers, environment detection logic, production safeguards (rate limiting, audit logging), staging parity with production, and development environment isolation. Essential for enterprise Clay deployments.
