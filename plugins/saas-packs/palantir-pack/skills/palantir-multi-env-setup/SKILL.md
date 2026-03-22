---
name: palantir-multi-env-setup
description: |
  Configure Palantir Foundry across development, staging, and production environments.
  Use when setting up multi-environment Foundry deployments, managing per-environment
  credentials, or implementing environment-specific configurations.
  Trigger with phrases like "palantir environments", "foundry staging",
  "foundry dev prod", "palantir environment setup".
allowed-tools: Read, Write, Edit, Bash(gcloud:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, environments, configuration]
compatible-with: claude-code, codex, openclaw
---

# Palantir Multi-Environment Setup

## Overview
Configure Foundry integrations across dev/staging/prod environments with separate credentials, enrollment hostnames, and scope policies per environment.

## Prerequisites
- Foundry enrollments for each environment (or separate projects within one enrollment)
- Secrets manager (AWS SM, GCP SM, or Vault)
- Familiarity with `palantir-security-basics`

## Instructions

### Step 1: Environment Configuration
```python
# src/config.py
import os
from dataclasses import dataclass

@dataclass
class FoundryEnvConfig:
    hostname: str
    client_id: str
    client_secret: str
    scopes: list[str]
    ontology: str

ENVIRONMENTS = {
    "development": FoundryEnvConfig(
        hostname=os.environ.get("DEV_FOUNDRY_HOSTNAME", "dev.palantirfoundry.com"),
        client_id=os.environ.get("DEV_FOUNDRY_CLIENT_ID", ""),
        client_secret=os.environ.get("DEV_FOUNDRY_CLIENT_SECRET", ""),
        scopes=["api:read-data"],  # Read-only in dev
        ontology="dev-ontology",
    ),
    "staging": FoundryEnvConfig(
        hostname=os.environ.get("STG_FOUNDRY_HOSTNAME", "staging.palantirfoundry.com"),
        client_id=os.environ.get("STG_FOUNDRY_CLIENT_ID", ""),
        client_secret=os.environ.get("STG_FOUNDRY_CLIENT_SECRET", ""),
        scopes=["api:read-data", "api:write-data"],
        ontology="staging-ontology",
    ),
    "production": FoundryEnvConfig(
        hostname=os.environ.get("PROD_FOUNDRY_HOSTNAME", "prod.palantirfoundry.com"),
        client_id=os.environ.get("PROD_FOUNDRY_CLIENT_ID", ""),
        client_secret=os.environ.get("PROD_FOUNDRY_CLIENT_SECRET", ""),
        scopes=["api:read-data", "api:write-data", "api:ontology-read"],
        ontology="production-ontology",
    ),
}

def get_config() -> FoundryEnvConfig:
    env = os.environ.get("ENVIRONMENT", "development")
    return ENVIRONMENTS[env]
```

### Step 2: Environment-Aware Client Factory
```python
import foundry

def create_client(config: FoundryEnvConfig) -> foundry.FoundryClient:
    auth = foundry.ConfidentialClientAuth(
        client_id=config.client_id,
        client_secret=config.client_secret,
        hostname=config.hostname,
        scopes=config.scopes,
    )
    auth.sign_in_as_service_user()
    return foundry.FoundryClient(auth=auth, hostname=config.hostname)

# Usage
config = get_config()
client = create_client(config)
```

### Step 3: Environment Variables per Platform
```bash
# Docker Compose
# docker-compose.yml
services:
  app:
    environment:
      - ENVIRONMENT=staging
      - STG_FOUNDRY_HOSTNAME=staging.palantirfoundry.com
      - STG_FOUNDRY_CLIENT_ID=${STG_CLIENT_ID}
      - STG_FOUNDRY_CLIENT_SECRET=${STG_CLIENT_SECRET}

# Kubernetes
kubectl create secret generic foundry-creds \
  --from-literal=hostname=prod.palantirfoundry.com \
  --from-literal=client-id=xxx \
  --from-literal=client-secret=yyy

# Cloud Run
gcloud run deploy my-app \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets "PROD_FOUNDRY_CLIENT_SECRET=foundry-secret:latest"
```

### Step 4: Environment Validation
```python
def validate_environment():
    """Verify current environment configuration is valid."""
    config = get_config()
    env = os.environ.get("ENVIRONMENT", "development")

    assert config.hostname, f"Missing hostname for {env}"
    assert config.client_id, f"Missing client_id for {env}"
    assert config.client_secret, f"Missing client_secret for {env}"

    # Verify connectivity
    client = create_client(config)
    ontologies = list(client.ontologies.Ontology.list())
    print(f"Environment {env}: connected to {config.hostname}")
    print(f"  Accessible ontologies: {[o.api_name for o in ontologies]}")
    return True
```

## Output
- Per-environment configuration with separate hostnames and credentials
- Environment-aware client factory
- Platform-specific deployment configuration
- Validation script for environment verification

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong environment data | Misconfigured `ENVIRONMENT` var | Verify env var matches expected |
| Cross-env credentials | Shared secrets | Ensure each env has unique credentials |
| Dev writing to prod | Wrong hostname | Enforce read-only scopes in dev |
| Missing secrets | Not deployed | Run validation script before deploying |

## Resources
- [Foundry Authentication](https://www.palantir.com/docs/foundry/api/general/overview/authentication)
- [Developer Console](https://www.palantir.com/docs/foundry/ontology-sdk/create-a-new-osdk)

## Next Steps
For deep migration strategies, see `palantir-migration-deep-dive`.
