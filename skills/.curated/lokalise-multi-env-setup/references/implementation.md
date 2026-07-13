# Lokalise Multi-Environment Setup -- Implementation Reference

## Overview

Configure separate Lokalise projects for development, staging, and production
environments with per-environment API tokens, project IDs, and sync policies.

## Prerequisites

- Separate Lokalise projects per environment (dev/staging/prod)
- Separate API tokens per environment
- Secrets manager (AWS Secrets Manager, GCP Secret Manager, or Vault)

## Environment Configuration

```yaml
# config/lokalise.yml
environments:
  development:
    project_id: "${LOKALISE_DEV_PROJECT_ID}"
    api_token: "${LOKALISE_DEV_API_TOKEN}"
    languages: [en, es, fr]
    auto_sync: true
    sync_interval_minutes: 30

  staging:
    project_id: "${LOKALISE_STAGING_PROJECT_ID}"
    api_token: "${LOKALISE_STAGING_API_TOKEN}"
    languages: [en, es, fr, de, ja]
    auto_sync: true
    sync_interval_minutes: 60

  production:
    project_id: "${LOKALISE_PROD_PROJECT_ID}"
    api_token: "${LOKALISE_PROD_API_TOKEN}"
    languages: [en, es, fr, de, ja, pt, zh]
    auto_sync: false  # Manual approval required for prod
    require_review: true
```

## Python Config Loader

```python
import os
import json
import urllib.request

_ENV_CONFIG = {
    "development": {
        "project_id": os.environ.get("LOKALISE_DEV_PROJECT_ID", ""),
        "api_token": os.environ.get("LOKALISE_DEV_API_TOKEN", ""),
    },
    "staging": {
        "project_id": os.environ.get("LOKALISE_STAGING_PROJECT_ID", ""),
        "api_token": os.environ.get("LOKALISE_STAGING_API_TOKEN", ""),
    },
    "production": {
        "project_id": os.environ.get("LOKALISE_PROD_PROJECT_ID", ""),
        "api_token": os.environ.get("LOKALISE_PROD_API_TOKEN", ""),
    },
}

def get_lokalise_config(env: str = None) -> dict:
    """Return Lokalise config for the given (or current) environment."""
    if env is None:
        env = os.environ.get("APP_ENV", "development")

    config = _ENV_CONFIG.get(env)
    if not config:
        raise ValueError(f"Unknown environment: {env!r}. Must be one of {list(_ENV_CONFIG)}")

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing env vars for {env}: {missing}")

    return {"env": env, **config}

def lokalise_request(method: str, path: str, env: str = None, payload: dict = None) -> dict:
    config = get_lokalise_config(env)
    headers = {
        "X-Api-Token": config["api_token"],
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f"https://api.lokalise.com/api2{path}",
        data=body,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def sync_translations(source_env: str, target_env: str, dry_run: bool = True) -> dict:
    """
    Sync approved translations from source environment to target.
    Useful for promoting staging -> production.
    """
    src_config = get_lokalise_config(source_env)
    tgt_config = get_lokalise_config(target_env)

    # Fetch keys from source
    src_result = lokalise_request("GET", f"/projects/{src_config['project_id']}/keys", source_env)
    src_keys = {k["key_name"]["web"]: k for k in src_result.get("keys", [])}

    # Fetch keys from target
    tgt_result = lokalise_request("GET", f"/projects/{tgt_config['project_id']}/keys", target_env)
    tgt_keys = {k["key_name"]["web"]: k for k in tgt_result.get("keys", [])}

    # Identify new keys not yet in target
    new_keys = set(src_keys) - set(tgt_keys)

    report = {
        "source": source_env,
        "target": target_env,
        "source_key_count": len(src_keys),
        "target_key_count": len(tgt_keys),
        "new_keys": list(new_keys),
        "dry_run": dry_run,
    }

    if not dry_run and new_keys:
        # Build payload to create missing keys in target
        keys_to_create = [src_keys[k] for k in new_keys]
        lokalise_request(
            "POST",
            f"/projects/{tgt_config['project_id']}/keys",
            target_env,
            {"keys": keys_to_create},
        )
        report["keys_created"] = len(keys_to_create)

    return report
```

## Per-Environment CI Workflow

```yaml
# .github/workflows/sync-translations.yml
name: Sync Translations

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options: [development, staging, production]

jobs:
  sync:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Install lokalise2 CLI
        run: |
          curl -sfL https://raw.githubusercontent.com/lokalise/lokalise-cli-2-go/master/install.sh | sh
          echo "$HOME/.lokalise" >> $GITHUB_PATH

      - name: Pull translations
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_API_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ secrets.LOKALISE_PROJECT_ID }}
          APP_ENV: ${{ github.event.inputs.environment }}
        run: |
          lokalise2 file download \
            --token="${LOKALISE_API_TOKEN}" \
            --project-id="${LOKALISE_PROJECT_ID}" \
            --format=json \
            --original-filenames=true \
            --dest=src/locales/
```

## Environment Variable Setup Script

```bash
#!/bin/bash
# setup-lokalise-envs.sh -- configure all environment secrets

set -euo pipefail

for ENV in development staging production; do
    echo "Setting up Lokalise config for: $ENV"

    read -rp "  ${ENV} API Token: " TOKEN
    read -rp "  ${ENV} Project ID: " PROJECT_ID

    # Store in AWS Secrets Manager
    if command -v aws &>/dev/null; then
        aws secretsmanager create-secret \
            --name "lokalise/${ENV}/api-token" \
            --secret-string "${TOKEN}" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "lokalise/${ENV}/api-token" \
            --secret-string "${TOKEN}"

        aws secretsmanager create-secret \
            --name "lokalise/${ENV}/project-id" \
            --secret-string "${PROJECT_ID}" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "lokalise/${ENV}/project-id" \
            --secret-string "${PROJECT_ID}"
    fi

    echo "  Stored ${ENV} secrets"
done
echo "Done."
```

## Resources

- [Lokalise API Reference](https://developers.lokalise.com/reference)
- [Lokalise CLI](https://developers.lokalise.com/reference/lokalise-cli)
- Lokalise Projects

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
