---
name: gh-actions-validator
description: |
  Automatically validates and enforces GitHub Actions best practices for Vertex AI and Google Cloud deployments.
  Expert in Workload Identity Federation (WIF), Vertex AI Agent Engine deployment pipelines, security validation, and CI/CD automation.
  Triggers: "create github actions", "deploy vertex ai", "setup wif", "validate github workflow", "gcp deployment pipeline"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## What This Skill Does

Expert validator and enforcer of GitHub Actions best practices specifically for Vertex AI Agent Engine and Google Cloud deployments. Ensures secure, production-ready CI/CD pipelines using Workload Identity Federation (WIF) instead of service account JSON keys.

## When This Skill Activates

### Trigger Phrases
- "Create GitHub Actions workflow for Vertex AI"
- "Deploy agent to Vertex AI Engine"
- "Set up Workload Identity Federation"
- "Validate GitHub Actions security for GCP"
- "GitHub Actions deployment pipeline"
- "WIF configuration for Google Cloud"
- "Automate Vertex AI deployment"
- "GitHub Actions best practices GCP"

### Use Cases
- Creating CI/CD pipelines for Vertex AI Agent Engine deployments
- Migrating from JSON service account keys to WIF
- Enforcing security best practices in GitHub Actions
- Validating post-deployment of Vertex AI agents
- Setting up automated monitoring for deployed agents
- Implementing OIDC-based authentication to Google Cloud

## Validation Rules Enforced

### 1. Workload Identity Federation (WIF) Mandatory

❌ **NEVER use JSON service account keys**:
```yaml
# ❌ FORBIDDEN - JSON keys are insecure
- name: Authenticate (INSECURE)
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}  # ❌ NEVER DO THIS
```

✅ **ALWAYS use WIF**:
```yaml
# ✅ REQUIRED - WIF with OIDC
permissions:
  contents: read
  id-token: write  # ✅ REQUIRED for WIF

- name: Authenticate (SECURE)
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
```

### 2. OIDC Permissions Required

❌ **Missing id-token permission**:
```yaml
# ❌ FAILS - Missing id-token: write
permissions:
  contents: read
```

✅ **Correct permissions**:
```yaml
# ✅ REQUIRED for WIF OIDC
permissions:
  contents: read
  id-token: write  # MUST be present
```

### 3. IAM Least Privilege

❌ **Overly permissive roles**:
```yaml
# ❌ FORBIDDEN - Too many permissions
roles:
  - roles/owner
  - roles/editor
```

✅ **Least privilege**:
```yaml
# ✅ REQUIRED - Minimal permissions
roles:
  - roles/run.admin
  - roles/iam.serviceAccountUser
  - roles/aiplatform.user
```

### 4. Vertex AI Agent Engine Deployment Validation

**Post-Deployment Checks** (MANDATORY):
```yaml
- name: Validate Agent Deployment
  run: |
    python scripts/validate-deployment.py \
      --project-id=${{ secrets.GCP_PROJECT_ID }} \
      --agent-id=production-agent

# Validation checklist:
# ✅ Agent state is RUNNING
# ✅ Code Execution Sandbox enabled (14-day TTL)
# ✅ Memory Bank configured
# ✅ A2A Protocol compliant (AgentCard accessible)
# ✅ Model Armor enabled (prompt injection protection)
# ✅ VPC Service Controls configured
# ✅ Service account has minimal IAM permissions
# ✅ Monitoring dashboards created
# ✅ Alerting policies configured
```

### 5. Security Scanning (REQUIRED)

```yaml
# ✅ REQUIRED - Security validation before deployment
- name: Scan for secrets
  uses: trufflesecurity/trufflehog@main

- name: Vulnerability scanning
  uses: aquasecurity/trivy-action@master

- name: Validate no service account keys
  run: |
    if find . -name "*service-account*.json"; then
      echo "❌ Service account JSON keys detected"
      exit 1
    fi
```

### 6. Agent Configuration Validation

**Before Deployment** (MANDATORY):
```python
def validate_agent_config(agent_config: dict) -> bool:
    """
    Validate agent configuration before deployment.
    """

    # ✅ Code Execution TTL must be 7-14 days
    ttl = agent_config.get("code_execution_config", {}).get("state_ttl_days")
    assert 7 <= ttl <= 14, "❌ State TTL must be 7-14 days"

    # ✅ Memory Bank must be enabled for stateful agents
    memory_enabled = agent_config.get("memory_bank_config", {}).get("enabled")
    assert memory_enabled, "❌ Memory Bank should be enabled"

    # ✅ Model Armor must be enabled (prompt injection protection)
    model_armor = agent_config.get("model_armor", {}).get("enabled")
    assert model_armor, "❌ Model Armor must be enabled"

    # ✅ VPC configuration required for enterprise
    vpc_config = agent_config.get("vpc_config")
    assert vpc_config, "❌ VPC configuration missing"

    # ✅ Auto-scaling configured
    auto_scaling = agent_config.get("auto_scaling")
    assert auto_scaling, "❌ Auto-scaling not configured"
    assert auto_scaling.get("min_instances") >= 1, "❌ min_instances < 1"

    return True
```

## Workflow Templates

### Template 1: Vertex AI Agent Engine Deployment

```yaml
name: Deploy Vertex AI Agent

on:
  push:
    branches: [main]
    paths:
      - 'agent/**'
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

env:
  AGENT_ID: 'production-adk-agent'
  REGION: 'us-central1'

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Authenticate to GCP (WIF)
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Validate Agent Configuration
        run: |
          python scripts/validate-agent-config.py

      - name: Deploy to Vertex AI Engine
        run: |
          python scripts/deploy-agent.py \
            --project-id=${{ secrets.GCP_PROJECT_ID }} \
            --location=${{ env.REGION }} \
            --agent-id=${{ env.AGENT_ID }}

      - name: Post-Deployment Validation
        run: |
          python scripts/validate-deployment.py \
            --project-id=${{ secrets.GCP_PROJECT_ID }} \
            --agent-id=${{ env.AGENT_ID }}

      - name: Setup Monitoring
        run: |
          python scripts/setup-monitoring.py \
            --project-id=${{ secrets.GCP_PROJECT_ID }} \
            --agent-id=${{ env.AGENT_ID }}

      - name: Test Agent Endpoint
        run: |
          python scripts/test-agent.py \
            --agent-id=${{ env.AGENT_ID }}
```

### Template 2: WIF Setup (One-Time Infrastructure)

```yaml
name: Setup Workload Identity Federation

on:
  workflow_dispatch:
    inputs:
      github_repo:
        description: 'GitHub repository (owner/repo)'
        required: true

permissions:
  contents: read

jobs:
  setup-wif:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Authenticate with JSON key (one-time only)
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SETUP_KEY }}

      - name: Run WIF setup script
        run: |
          bash scripts/setup-wif.sh \
            --project-id=${{ secrets.GCP_PROJECT_ID }} \
            --github-repo=${{ github.event.inputs.github_repo }}

      - name: Output WIF configuration
        run: |
          cat wif-config.txt
```

### Template 3: Security Validation (Pre-Deployment)

```yaml
name: Security Validation

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  security-checks:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

      - name: Vulnerability scanning
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Validate no service account keys
        run: |
          if find . -name "*service-account*.json" -o -name "*credentials*.json"; then
            echo "❌ Service account key files detected"
            exit 1
          fi
          echo "✅ No service account keys found"

      - name: Validate WIF usage in workflows
        run: |
          if grep -r "credentials_json" .github/workflows/; then
            echo "❌ JSON credentials detected (use WIF)"
            exit 1
          fi
          echo "✅ Workflows use WIF"

      - name: Validate IAM roles (no owner/editor)
        run: |
          if grep -r "roles/owner\|roles/editor" . --include="*.tf" --include="*.yaml"; then
            echo "❌ Overly permissive IAM roles detected"
            exit 1
          fi
          echo "✅ Least privilege IAM roles"
```

## Vertex AI Agent Engine Specific Validations

### Deployment Configuration Validation

```python
# scripts/validate-agent-config.py
from typing import Dict, Any

def validate_vertex_agent_config(config: Dict[str, Any]) -> None:
    """
    Comprehensive Vertex AI Agent Engine configuration validation.
    """

    # 1. Model Selection
    model = config.get("model")
    assert model in ["gemini-2.5-pro", "gemini-2.5-flash"], \
        f"❌ Invalid model: {model}. Use gemini-2.5-pro or gemini-2.5-flash"

    # 2. Code Execution Sandbox
    code_exec = config.get("code_execution_config", {})
    if code_exec.get("enabled"):
        ttl = code_exec.get("state_ttl_days")
        assert 1 <= ttl <= 14, \
            f"❌ State TTL must be 1-14 days, got {ttl}"

        assert code_exec.get("sandbox_type") == "SECURE_ISOLATED", \
            "❌ Sandbox type must be SECURE_ISOLATED"

        timeout = code_exec.get("timeout_seconds")
        assert 1 <= timeout <= 600, \
            f"❌ Timeout must be 1-600 seconds, got {timeout}"

    # 3. Memory Bank
    memory = config.get("memory_bank_config", {})
    if memory.get("enabled"):
        max_memories = memory.get("max_memories")
        assert max_memories >= 100, \
            f"⚠️ Low memory limit: {max_memories}. Recommend >= 100"

        assert memory.get("indexing_enabled"), \
            "⚠️ Indexing disabled will slow query performance"

        assert memory.get("auto_cleanup"), \
            "⚠️ Auto-cleanup disabled may exceed quotas"

    # 4. Security
    assert config.get("model_armor", {}).get("enabled"), \
        "❌ Model Armor must be enabled (prompt injection protection)"

    assert config.get("vpc_config"), \
        "❌ VPC configuration required for enterprise deployment"

    # 5. Auto-Scaling
    auto_scaling = config.get("auto_scaling", {})
    assert auto_scaling.get("min_instances") >= 1, \
        "❌ min_instances must be >= 1 for production"

    assert auto_scaling.get("max_instances") >= 3, \
        "⚠️ max_instances should be >= 3 for high availability"

    # 6. IAM
    sa = config.get("service_account")
    assert sa and "@" in sa, \
        f"❌ Invalid service account: {sa}"

    print("✅ All Vertex AI agent configuration checks passed")
```

### Post-Deployment Health Check

```python
# scripts/validate-deployment.py
from google.cloud.aiplatform import agent_builder
import requests

def validate_vertex_deployment(
    project_id: str,
    location: str,
    agent_id: str
) -> bool:
    """
    Post-deployment validation for Vertex AI Agent Engine.
    """

    client = agent_builder.AgentBuilderClient()
    agent_name = f"projects/{project_id}/locations/{location}/agents/{agent_id}"

    # 1. Agent Status
    agent = client.get_agent(name=agent_name)
    assert agent.state == "RUNNING", \
        f"❌ Agent not running: {agent.state}"
    print(f"✅ Agent status: {agent.state}")

    # 2. Code Execution Sandbox
    assert agent.code_execution_config.enabled, \
        "❌ Code Execution not enabled"
    print(f"✅ Code Execution enabled (TTL: {agent.code_execution_config.state_ttl_days} days)")

    # 3. Memory Bank
    assert agent.memory_bank_config.enabled, \
        "❌ Memory Bank not enabled"
    print(f"✅ Memory Bank enabled")

    # 4. A2A Protocol Compliance
    agentcard_url = f"{agent.agent_endpoint}/.well-known/agent-card"
    response = requests.get(agentcard_url, timeout=10)
    assert response.status_code == 200, \
        f"❌ AgentCard not accessible: {response.status_code}"

    agentcard = response.json()
    assert "name" in agentcard and "version" in agentcard, \
        "❌ AgentCard missing required fields"
    print(f"✅ A2A Protocol: AgentCard accessible")

    # 5. Model Armor
    assert agent.model_armor.enabled, \
        "❌ Model Armor not enabled"
    print(f"✅ Model Armor enabled (prompt injection protection)")

    # 6. Endpoint
    assert agent.agent_endpoint, \
        "❌ Agent endpoint not available"
    print(f"✅ Agent endpoint: {agent.agent_endpoint}")

    # 7. Service Account
    assert agent.service_account, \
        "❌ Service account not configured"
    print(f"✅ Service account: {agent.service_account}")

    print("\n✅ All post-deployment validations passed!")
    return True
```

## Tool Permissions

This skill uses:
- **Read**: Analyze workflow files and configurations
- **Write**: Create GitHub Actions workflows
- **Edit**: Update existing workflows for compliance
- **Grep**: Search for security issues (JSON keys, etc.)
- **Glob**: Find workflow files across repository
- **Bash**: Execute validation scripts and gcloud commands

## Integration with Other Plugins

### Works with jeremy-adk-orchestrator
- Provides CI/CD for ADK agent deployments
- Automates A2A protocol validation
- Ensures production readiness

### Works with jeremy-vertex-validator
- GitHub Actions calls vertex-validator for post-deployment checks
- Comprehensive validation pipeline
- Production readiness scoring

### Works with jeremy-adk-terraform
- GitHub Actions deploys Terraform infrastructure
- Automated infrastructure provisioning
- Validation of Terraform-provisioned resources

### Works with jeremy-vertex-engine
- GitHub Actions triggers vertex-engine-inspector
- Continuous health monitoring
- Automated compliance checks

## Best Practices Summary

### Security (MANDATORY)
✅ Use WIF (Workload Identity Federation) - never JSON keys
✅ Require `id-token: write` permission for OIDC
✅ IAM least privilege (never owner/editor roles)
✅ Attribute-based access control (restrict by repository)
✅ Enable Model Armor for agents
✅ VPC Service Controls for enterprise isolation
✅ Scan for secrets in code (Trufflehog)
✅ Vulnerability scanning (Trivy)

### Vertex AI Specific (MANDATORY)
✅ Code Execution Sandbox: 7-14 day TTL
✅ Memory Bank enabled for stateful agents
✅ A2A Protocol compliance (AgentCard validation)
✅ Model Armor enabled (prompt injection protection)
✅ Auto-scaling configured (min >= 1, max >= 3)
✅ Post-deployment validation (agent status, endpoints)
✅ Monitoring dashboards created
✅ Alerting policies configured

### CI/CD (RECOMMENDED)
✅ Conditional job execution (only on relevant paths)
✅ Caching for dependencies (faster builds)
✅ Concurrent jobs when possible
✅ Rollback strategies for failed deployments
✅ Health check endpoints

## Version History

- **1.0.0** (2025): Initial release with WIF enforcement, Vertex AI validations, security scanning

## References

- **Workload Identity Federation**: https://cloud.google.com/iam/docs/workload-identity-federation
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **google-github-actions/auth**: https://github.com/google-github-actions/auth
