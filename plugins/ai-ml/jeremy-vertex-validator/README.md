# Jeremy Vertex Validator

**🎯 VERTEX AI AGENT ENGINE DEPLOYMENT VALIDATION**

Production readiness validator for **Vertex AI Agent Engine** deployments. Validates ADK agents before production deployment with comprehensive security, compliance, monitoring, and performance checks.

## ⚠️ Important: What This Plugin Is For

**✅ THIS PLUGIN IS FOR:**
- **Vertex AI Agent Engine** deployment validation (fully-managed runtime)
- **ADK agents** deployed to Agent Engine
- **Pre-deployment validation** of agent code and configuration
- **Production readiness checks** for Agent Engine features
- Security, compliance, monitoring, and performance validation

**❌ THIS PLUGIN IS NOT FOR:**
- Cloud Run deployment validation (use Cloud Run-specific tools)
- LangChain/LlamaIndex on other platforms
- Self-hosted agent infrastructure validation
- Non-Agent Engine deployments

## Overview

This plugin performs comprehensive production readiness validation for ADK agents before deploying to Vertex AI Agent Engine. It checks security posture, compliance requirements, monitoring configuration, performance optimization, and best practices enforcement.

**Validation Categories:**
- Security: IAM, VPC-SC, encryption, Model Armor
- Monitoring: Dashboards, alerts, SLOs, token tracking
- Performance: Auto-scaling, caching, resource limits
- Compliance: Audit logging, data residency, backups
- Best Practices: Agent Engine configuration, Memory Bank, Code Execution Sandbox

## Installation

```bash
/plugin install jeremy-vertex-validator@claude-code-plugins-plus
```

## Prerequisites & Dependencies

### Required Google Cloud Setup

**1. Google Cloud Project with APIs Enabled:**
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    securitycenter.googleapis.com \
    --project=YOUR_PROJECT_ID
```

**2. Authentication:**
```bash
# Application Default Credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**3. Required IAM Permissions:**
```yaml
# Minimum required roles for validation:
- roles/aiplatform.user              # Query Agent Engine resources
- roles/discoveryengine.viewer       # View agent configurations
- roles/logging.viewer               # Read audit logs
- roles/monitoring.viewer            # Access metrics and alerts
- roles/iam.securityReviewer         # Review IAM policies
- roles/cloudtrace.user              # View trace data
```

### Required Python Packages

**Install via pip:**
```bash
# Core Vertex AI SDK (with Agent Engine support)
pip install google-cloud-aiplatform[agent_engines]>=1.120.0

# ADK SDK (for agent validation)
pip install google-adk>=1.15.1

# Observability & Monitoring
pip install google-cloud-logging>=3.10.0
pip install google-cloud-monitoring>=2.21.0
pip install google-cloud-trace>=1.13.0

# Security & Compliance
pip install google-cloud-security-center>=1.28.0
pip install google-cloud-asset>=3.20.0

# Code Analysis
pip install pylint>=3.0.0
pip install flake8>=7.0.0
pip install mypy>=1.8.0
```

**All dependencies at once:**
```bash
pip install --upgrade \
    'google-cloud-aiplatform[agent_engines]>=1.120.0' \
    'google-adk>=1.15.1' \
    'google-cloud-logging>=3.10.0' \
    'google-cloud-monitoring>=2.21.0' \
    'google-cloud-trace>=1.13.0' \
    'google-cloud-security-center>=1.28.0' \
    'google-cloud-asset>=3.20.0' \
    'pylint>=3.0.0' \
    'flake8>=7.0.0' \
    'mypy>=1.8.0'
```

### Required gcloud CLI Tools

**Install gcloud CLI:**
```bash
# Install gcloud (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Update to latest version
gcloud components update

# Install alpha commands (for Agent Engine)
gcloud components install alpha

# Install beta commands (for Security Command Center)
gcloud components install beta
```

**Verify Installation:**
```bash
gcloud --version
# Should show: Google Cloud SDK 450.0.0+ (or higher)

# Test Agent Engine access
gcloud alpha ai agent-engines list --location=us-central1 --project=YOUR_PROJECT_ID

# Test Security Command Center access
gcloud scc findings list organizations/YOUR_ORG_ID --limit=1
```

### What Gets Validated

**This plugin validates agents deployed to Agent Engine via:**

1. **ADK CLI Deployment:**
```bash
adk deploy \
    --project=YOUR_PROJECT_ID \
    --location=us-central1 \
    --agent-id=my-adk-agent \
    --source=./agent-code/
```

2. **Python SDK Deployment:**
```python
from google.adk import Agent
from google.cloud import aiplatform

agent = Agent(
    name="my-adk-agent",
    tools=[...],
    model="gemini-2.0-flash-001"
)

deployment = client.agent_engines.deploy(
    agent=agent,
    config={"agent_framework": "google-adk"}
)
```

3. **Terraform Deployment:**
```hcl
resource "google_vertex_ai_reasoning_engine" "agent" {
  display_name = "my-adk-agent"
  region       = "us-central1"

  spec {
    agent_framework = "google-adk"
    # ... agent configuration
  }
}
```

### ❌ NOT Compatible With

- **Cloud Run deployments** (different runtime, use Cloud Run validation tools)
- **LangChain on non-Agent Engine platforms** (not ADK)
- **LlamaIndex custom servers** (not Agent Engine)
- **Self-hosted agent infrastructure** (requires custom validation)

## Features

✅ **Security Validation**: IAM roles, VPC-SC, encryption, Model Armor, service accounts
✅ **Compliance Checks**: Audit logging, data residency, privacy policies, backups
✅ **Monitoring Verification**: Dashboards, alerts, SLOs, token tracking, error rates
✅ **Performance Validation**: Auto-scaling, caching, resource limits, Code Execution TTL
✅ **Best Practices Enforcement**: Agent Engine configuration, Memory Bank, A2A protocol
✅ **Code Quality Checks**: Linting, type checking, security scanning
✅ **Production Readiness Scoring**: Weighted checklist with pass/fail/warning status

## Components

### Skills (Auto-Activating)
- **validator-expert**: Triggers on "validate deployment", "production readiness check", "security audit"
  - **Tool Permissions**: Read, Grep, Glob, Bash (read-only analysis)
  - **Version**: 1.0.0 (2025 schema compliant)

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Validate my ADK agent deployment for production"
"Run production readiness check on agent-xyz"
"Security audit for Vertex AI Agent Engine deployment"
"Check compliance for this agent configuration"
"Validate agent before deploying to production"
```

The skill auto-activates and performs comprehensive validation with a detailed report.

### What Gets Validated

The validator performs checks across 5 categories:

## Validation Checklist

### 1. Security Validation (30% weight)

**IAM & Access Control:**
- ✅ Service accounts follow least privilege principle
- ✅ No overly permissive roles (Owner, Editor)
- ✅ Workload Identity configured for multi-cloud
- ✅ API keys rotated regularly
- ✅ No hardcoded credentials in code

**Network Security:**
- ✅ VPC Service Controls enabled for Agent Engine
- ✅ Private IP addressing configured
- ✅ Firewall rules follow allowlist approach
- ✅ TLS 1.3 enforced for all connections

**Data Protection:**
- ✅ Encryption at rest with CMEK keys
- ✅ Encryption in transit (TLS)
- ✅ Model Armor enabled (prompt injection protection)
- ✅ Sensitive data handling complies with policies

**Example Validation:**
```python
def validate_security(agent_config):
    """Run security validation checks."""
    checks = []

    # Check IAM roles
    service_account = agent_config.get('service_account')
    if has_overly_permissive_roles(service_account):
        checks.append({
            "category": "Security",
            "check": "IAM Least Privilege",
            "status": "FAIL",
            "message": f"Service account {service_account} has Owner role"
        })

    # Check encryption
    if not agent_config.get('encryption_config', {}).get('cmek_key'):
        checks.append({
            "category": "Security",
            "check": "Encryption at Rest",
            "status": "WARNING",
            "message": "No CMEK key configured, using Google-managed keys"
        })

    # Check Model Armor
    if agent_config.get('agent_framework') == 'google-adk':
        if not agent_config.get('model_armor_enabled'):
            checks.append({
                "category": "Security",
                "check": "Model Armor",
                "status": "FAIL",
                "message": "Model Armor not enabled for ADK agent"
            })

    return checks
```

### 2. Monitoring Validation (20% weight)

**Observability Dashboard:**
- ✅ Agent Engine observability dashboard configured
- ✅ Token usage tracking enabled
- ✅ Error rate monitoring active
- ✅ Latency metrics (p50, p90, p95, p99) tracked

**Alerting:**
- ✅ Alert policies configured for critical errors
- ✅ Notification channels set up
- ✅ Alert thresholds appropriate
- ✅ Alert escalation policies defined

**SLOs & SLIs:**
- ✅ Service Level Objectives defined
- ✅ Error budget configured
- ✅ SLI metrics tracked
- ✅ SLO compliance reporting enabled

**Logging:**
- ✅ Cloud Logging enabled for Agent Engine
- ✅ Log retention policies configured (>90 days)
- ✅ Structured logging format used
- ✅ PII data properly redacted in logs

**Example Validation:**
```python
def validate_monitoring(agent_id, project_id):
    """Check monitoring configuration."""
    from google.cloud import monitoring_v3

    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    # Check for agent-specific alert policies
    alert_policies = client.list_alert_policies(name=project_name)

    agent_alerts = [
        policy for policy in alert_policies
        if agent_id in policy.display_name.lower()
    ]

    if not agent_alerts:
        return {
            "category": "Monitoring",
            "check": "Alert Policies",
            "status": "FAIL",
            "message": f"No alert policies configured for agent {agent_id}"
        }

    return {
        "category": "Monitoring",
        "check": "Alert Policies",
        "status": "PASS",
        "message": f"Found {len(agent_alerts)} alert policies"
    }
```

### 3. Performance Validation (25% weight)

**Auto-Scaling:**
- ✅ Auto-scaling enabled for Agent Engine
- ✅ Min/max replicas configured appropriately
- ✅ CPU/memory targets set
- ✅ Scale-up/scale-down thresholds tuned

**Caching:**
- ✅ Memory Bank caching enabled
- ✅ Cache hit rate >60%
- ✅ Cache TTL configured
- ✅ Response caching for frequent queries

**Resource Limits:**
- ✅ Memory limits appropriate for workload
- ✅ CPU allocation sufficient
- ✅ Timeout values configured
- ✅ Concurrent request limits set

**Code Execution Sandbox:**
- ✅ Sandbox state persistence TTL configured (1-14 days)
- ✅ Execution timeout appropriate
- ✅ Artifact storage configured
- ✅ Resource isolation enabled

**Example Validation:**
```python
def validate_performance(agent_config):
    """Check performance configuration."""
    checks = []

    # Check auto-scaling
    runtime_config = agent_config.get('runtime_config', {})
    auto_scaling = runtime_config.get('auto_scaling', {})

    if not auto_scaling.get('enabled'):
        checks.append({
            "category": "Performance",
            "check": "Auto-Scaling",
            "status": "WARNING",
            "message": "Auto-scaling not enabled"
        })

    # Check Code Execution Sandbox TTL
    code_exec = runtime_config.get('code_execution_config', {})
    ttl_days = code_exec.get('state_persistence_ttl_days', 0)

    if ttl_days < 1 or ttl_days > 14:
        checks.append({
            "category": "Performance",
            "check": "Code Execution TTL",
            "status": "FAIL",
            "message": f"TTL must be 1-14 days, got {ttl_days}"
        })

    return checks
```

### 4. Compliance Validation (15% weight)

**Audit Logging:**
- ✅ Cloud Audit Logs enabled
- ✅ Admin activity logged
- ✅ Data access logs enabled for sensitive operations
- ✅ Log retention >1 year for compliance

**Data Residency:**
- ✅ Agent deployed in compliant region
- ✅ Data storage in approved locations
- ✅ Cross-border data transfer documented
- ✅ Regional data processing requirements met

**Privacy:**
- ✅ PII handling policies implemented
- ✅ User consent mechanisms in place
- ✅ Data anonymization for non-prod
- ✅ Right to deletion implemented

**Backup & DR:**
- ✅ Memory Bank backup configured
- ✅ Disaster recovery plan documented
- ✅ RTO/RPO objectives defined
- ✅ Backup restoration tested

**Example Validation:**
```python
def validate_compliance(agent_config, project_id):
    """Check compliance requirements."""
    from google.cloud import logging_v2

    # Check audit logging
    client = logging_v2.ConfigServiceV2Client()
    parent = f"projects/{project_id}"

    sinks = client.list_sinks(parent=parent)
    audit_sink_exists = any(
        'audit' in sink.name.lower()
        for sink in sinks
    )

    if not audit_sink_exists:
        return {
            "category": "Compliance",
            "check": "Audit Logging",
            "status": "FAIL",
            "message": "No audit log sink configured"
        }

    return {
        "category": "Compliance",
        "check": "Audit Logging",
        "status": "PASS",
        "message": "Audit logging configured"
    }
```

### 5. Best Practices Validation (10% weight)

**Agent Configuration:**
- ✅ Model selection appropriate for use case
- ✅ System instructions clear and specific
- ✅ Tool definitions follow best practices
- ✅ Error handling implemented

**Memory Bank:**
- ✅ Memory Bank enabled for stateful interactions
- ✅ Retention policy configured
- ✅ Indexing strategy optimized
- ✅ Query performance acceptable

**A2A Protocol:**
- ✅ AgentCard published and accessible
- ✅ Input/output schemas defined
- ✅ Task API endpoints functional
- ✅ Session management implemented

**Code Quality:**
- ✅ Linting passes (pylint/flake8)
- ✅ Type checking passes (mypy)
- ✅ No security vulnerabilities (bandit)
- ✅ Test coverage >65%

**Example Validation:**
```bash
# Run code quality checks
pylint agent_code/ --fail-under=8.0
flake8 agent_code/ --max-line-length=100
mypy agent_code/ --strict
bandit -r agent_code/ -ll

# Check test coverage
pytest --cov=agent_code --cov-report=term-missing --cov-fail-under=65
```

## Production Readiness Report

### Report Format

The validator generates a comprehensive report with:

1. **Executive Summary**
   - Overall readiness score (0-100%)
   - Status: PRODUCTION READY / NEEDS IMPROVEMENT / NOT READY
   - Critical issues count
   - Warnings count

2. **Category Scores**
   - Security: X/100 (30% weight)
   - Monitoring: X/100 (20% weight)
   - Performance: X/100 (25% weight)
   - Compliance: X/100 (15% weight)
   - Best Practices: X/100 (10% weight)

3. **Detailed Findings**
   - PASS checks (green)
   - WARNING checks (yellow)
   - FAIL checks (red)

4. **Recommendations**
   - Prioritized action items
   - Implementation guidance
   - Timeline suggestions

### Example Report

```
==========================================================
PRODUCTION READINESS VALIDATION REPORT
==========================================================

Agent: sentiment-analysis-agent
Agent ID: projects/my-project/locations/us-central1/reasoningEngines/12345
Validated: 2025-11-13 10:30:00 UTC

----------------------------------------------------------
OVERALL SCORE: 82% - NEEDS IMPROVEMENT
----------------------------------------------------------

Security:       85/100  (30% weight) → 25.5 points
Monitoring:     75/100  (20% weight) → 15.0 points
Performance:    88/100  (25% weight) → 22.0 points
Compliance:     70/100  (15% weight) → 10.5 points
Best Practices: 90/100  (10% weight) →  9.0 points
                                       ------
                                TOTAL:  82.0/100

----------------------------------------------------------
VALIDATION SUMMARY
----------------------------------------------------------

✅ PASS:    24 checks
⚠️  WARNING: 6 checks
❌ FAIL:    2 checks

----------------------------------------------------------
CRITICAL ISSUES (MUST FIX BEFORE PRODUCTION)
----------------------------------------------------------

❌ Security: Model Armor not enabled
   Impact: HIGH
   Fix: Add "model_armor_enabled": true to agent config

❌ Monitoring: No alert policies configured
   Impact: MEDIUM
   Fix: Create alert policies for error rate >5% and latency p95 >10s

----------------------------------------------------------
WARNINGS (RECOMMENDED IMPROVEMENTS)
----------------------------------------------------------

⚠️  Security: No CMEK key configured
   Impact: LOW
   Fix: Configure Customer-Managed Encryption Keys

⚠️  Performance: Memory Bank cache hit rate only 45%
   Impact: MEDIUM
   Fix: Review indexing strategy and cache TTL

⚠️  Compliance: Audit log retention only 30 days
   Impact: MEDIUM
   Fix: Increase retention to 1 year for compliance

⚠️  Best Practices: Test coverage 52% (target: 65%)
   Impact: LOW
   Fix: Add unit tests for error handling paths

----------------------------------------------------------
RECOMMENDATIONS
----------------------------------------------------------

Priority 1 (Critical - Block Deployment):
1. Enable Model Armor to protect against prompt injection attacks
2. Configure alert policies for production monitoring

Priority 2 (High - Fix Before Launch):
3. Increase audit log retention to 1 year
4. Improve Memory Bank cache hit rate to >60%

Priority 3 (Medium - Post-Launch):
5. Configure CMEK keys for enhanced data protection
6. Increase test coverage to 65%+

----------------------------------------------------------
NEXT STEPS
----------------------------------------------------------

1. Address 2 critical issues (estimated: 2 hours)
2. Review and fix 6 warnings (estimated: 1 day)
3. Re-run validation: jeremy-vertex-validator
4. Deploy to staging for integration testing
5. Final production validation before go-live

==========================================================
```

## Integration with Other Plugins

### jeremy-vertex-engine
- Validator checks agent config → Engine inspector monitors runtime
- Pre-deployment validation → Post-deployment inspection

### jeremy-adk-orchestrator
- Validator checks agents → Orchestrator coordinates validated agents
- Code validation → A2A protocol communication

### jeremy-adk-terraform
- Validator reviews Terraform configs → Terraform provisions infrastructure
- Pre-deployment validation → Infrastructure deployment

## Use Cases

### Pre-Deployment Validation
```
"Validate this ADK agent before production deployment"
"Run production readiness check on agent-xyz"
```

### Security Audits
```
"Security audit for Vertex AI Agent Engine deployment"
"Check IAM permissions and VPC-SC configuration"
```

### Compliance Verification
```
"Check compliance for this agent configuration"
"Validate audit logging and data residency requirements"
```

### Performance Review
```
"Review performance configuration for agent"
"Check auto-scaling and caching settings"
```

### Continuous Validation
```
"Run weekly validation on production agents"
"Monitor production readiness score over time"
```

## Requirements

- Google Cloud Project with Vertex AI enabled
- ADK agents targeted for Agent Engine deployment (NOT Cloud Run)
- Appropriate IAM permissions for validation
- Python 3.10+ for running validation scripts
- gcloud CLI with alpha components
- Cloud Logging and Monitoring enabled
- Security Command Center enabled (for security validation)

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.0 (2025) - Agent Engine production readiness validation
