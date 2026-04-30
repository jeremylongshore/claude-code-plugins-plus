---
name: oraclecloud-ci-integration
description: 'Configure CI/CD pipelines for OCI with Terraform and GitHub Actions.

  Use when setting up automated infrastructure deployments, running Terraform plans
  in CI, or configuring OCI authentication for GitHub Actions.

  Trigger with "oraclecloud ci", "oci terraform ci", "oci github actions", "oracle
  cloud ci integration".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(terraform:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud CI Integration

## Overview

Set up GitHub Actions workflows that authenticate to OCI, run Terraform plans, and execute tests against OCI services. The OCI Terraform provider has known bugs — notably ResourcePrincipal forcing the wrong region (#1761) — that require specific workarounds. This skill provides battle-tested CI patterns that avoid those pitfalls.

**Purpose:** Get a working CI pipeline that authenticates to OCI, runs Terraform safely, and tests OCI-dependent code without flaky failures.

## Prerequisites

- **OCI tenancy** with an API signing key configured in `~/.oci/config`
- **Terraform >= 1.5** and the OCI provider (`oracle/oci`)
- **GitHub repository** with Actions enabled
- **GitHub Secrets** configured: `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_TENANCY_OCID`, `OCI_REGION`, `OCI_PRIVATE_KEY` (PEM contents, base64-encoded)
- **Python 3.8+** with `pip install oci` for SDK-based tests

## Instructions

### Step 1: Configure GitHub Secrets for OCI Auth

OCI API key authentication requires five values. Store them as GitHub repository secrets:

```bash
# Encode your private key for safe storage in GitHub Secrets
base64 -w 0 ~/.oci/oci_api_key.pem
# Copy output → GitHub Settings > Secrets > OCI_PRIVATE_KEY
```

The remaining secrets come from your `~/.oci/config` file: `user`, `fingerprint`, `tenancy`, and `region`.

### Step 2: GitHub Actions Workflow with Terraform

Create `.github/workflows/oci-terraform.yml`:

```yaml
name: OCI Terraform
on:
  push:
    branches: [main]
  pull_request:

env:
  TF_VAR_tenancy_ocid: ${{ secrets.OCI_TENANCY_OCID }}
  TF_VAR_user_ocid: ${{ secrets.OCI_USER_OCID }}
  TF_VAR_fingerprint: ${{ secrets.OCI_FINGERPRINT }}
  TF_VAR_region: ${{ secrets.OCI_REGION }}

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Write OCI private key
        run: |
          echo "${{ secrets.OCI_PRIVATE_KEY }}" | base64 -d > /tmp/oci_key.pem
          chmod 600 /tmp/oci_key.pem

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.7.0"

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -out=tfplan
        env:
          TF_VAR_private_key_path: /tmp/oci_key.pem
```

### Step 3: Terraform Provider Configuration

Configure the OCI provider with explicit region to avoid the ResourcePrincipal region bug (#1761):

```hcl
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  user_ocid    = var.user_ocid
  fingerprint  = var.fingerprint
  private_key_path = var.private_key_path
  # CRITICAL: Always set region explicitly.
  # ResourcePrincipal auth can force the wrong region (#1761).
  region       = var.region
}

variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" { default = "us-ashburn-1" }
```

### Step 4: OCI CLI Commands in CI

For non-Terraform CI tasks, use the OCI CLI directly:

```yaml
      - name: Install OCI CLI
        run: |
          pip install oci-cli
          mkdir -p ~/.oci
          echo "${{ secrets.OCI_PRIVATE_KEY }}" | base64 -d > ~/.oci/oci_api_key.pem
          chmod 600 ~/.oci/oci_api_key.pem
          cat > ~/.oci/config << EOF
          [DEFAULT]
          user=${{ secrets.OCI_USER_OCID }}
          fingerprint=${{ secrets.OCI_FINGERPRINT }}
          tenancy=${{ secrets.OCI_TENANCY_OCID }}
          region=${{ secrets.OCI_REGION }}
          key_file=~/.oci/oci_api_key.pem
          EOF

      - name: List compute instances
        run: oci compute instance list --compartment-id ${{ secrets.OCI_TENANCY_OCID }}
```

### Step 5: Python SDK Tests with Mocks

Write testable OCI code by mocking the SDK clients:

```python
import oci
from unittest.mock import MagicMock, patch

def list_instances(compartment_id: str) -> list:
    """List all compute instances in a compartment."""
    config = oci.config.from_file("~/.oci/config")
    client = oci.core.ComputeClient(config)
    response = client.list_instances(compartment_id=compartment_id)
    return response.data

@patch("oci.core.ComputeClient")
@patch("oci.config.from_file")
def test_list_instances(mock_config, mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.list_instances.return_value.data = [
        MagicMock(display_name="web-server-1", lifecycle_state="RUNNING")
    ]
    instances = list_instances("ocid1.compartment.oc1..example")
    assert len(instances) == 1
    assert instances[0].display_name == "web-server-1"
```

## Output

Successful completion produces:
- A GitHub Actions workflow that authenticates to OCI using API key secrets
- Terraform provider configuration with the explicit region workaround
- OCI CLI setup steps for non-Terraform CI tasks
- A test pattern using mocked OCI SDK clients for unit testing

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad API key or wrong fingerprint | Verify secrets match `~/.oci/config` values exactly |
| NotAuthorizedOrNotFound | 404 | IAM policy missing or wrong OCID | Add required IAM policy for the API key user |
| Provider crash on plan | N/A | ResourcePrincipal region bug (#1761) | Always set `region` explicitly in provider block |
| TooManyRequests | 429 | Rate limited (no Retry-After header) | Add retry logic with exponential backoff |
| CERTIFICATE_VERIFY_FAILED | N/A | SSL cert issue in CI runner | Run `pip install certifi` and set `REQUESTS_CA_BUNDLE` |
| Terraform init fails | N/A | Provider version mismatch | Pin provider version: `version = ">= 5.0.0"` |

## Examples

**Quick OCI auth test in CI:**

```bash
# Verify OCI credentials work in a GitHub Actions step
pip install oci
python3 -c "
import oci
config = oci.config.from_file('~/.oci/config')
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config['user']).data
print(f'Authenticated as: {user.name}')
"
```

**Terraform plan with JSON output for PR comments:**

```bash
terraform plan -out=tfplan
terraform show -json tfplan | python3 -c "
import sys, json
plan = json.load(sys.stdin)
changes = plan.get('resource_changes', [])
adds = sum(1 for c in changes if 'create' in c['change']['actions'])
dels = sum(1 for c in changes if 'delete' in c['change']['actions'])
print(f'Plan: +{adds} -{dels} resources')
"
```

## Resources

- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — official provider documentation
- [OCI API Reference](https://docs.oracle.com/en-us/iaas/api/) — REST API specs for all services
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — SDK reference and examples
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line tool docs
- [OCI SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common error resolution

## Next Steps

After CI is working, proceed to `oraclecloud-deploy-integration` to set up container deployments via OKE or Container Instances, or see `oraclecloud-observability` to add monitoring to your CI-deployed infrastructure.
