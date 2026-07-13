# Examples — Vertex Engine Inspector

## Example 1: Pre-Production Readiness Check

Run all 28 checklist items against a newly deployed ADK agent before production launch.

### Running the Inspection

```python
# Authenticate and connect via Python SDK
# (There is NO gcloud CLI for Agent Engine — use the SDK)
import vertexai

client = vertexai.Client(project="my-gcp-project", location="us-central1")

# List available agent engines to find the target
for engine in client.agent_engines.list():
    print(f"{engine.name}  {engine.display_name}  {engine.state}")
# projects/my-gcp-project/locations/us-central1/reasoningEngines/001    data-analyst       ACTIVE
# projects/my-gcp-project/locations/us-central1/reasoningEngines/002    support-bot        ACTIVE

# Get agent engine details
engine = client.agent_engines.get(
    name="projects/my-gcp-project/locations/us-central1/reasoningEngines/001"
)
print(engine)
```

### Inspection Script

```python
# inspect_agent.py
import subprocess
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class CheckResult:
    name: str
    category: str
    status: str  # PASS, FAIL, WARN, SKIP
    score: float  # 0.0 - 1.0
    detail: str
    recommendation: Optional[str] = None

@dataclass
class InspectionReport:
    agent_name: str
    project_id: str
    region: str
    overall_score: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    checks: List[CheckResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

# Category weights for overall score
CATEGORY_WEIGHTS = {
    "runtime": 0.10,
    "code_execution": 0.15,
    "memory_bank": 0.10,
    "a2a_protocol": 0.10,
    "security": 0.25,
    "performance": 0.15,
    "monitoring": 0.15,
}


def get_agent_engine(project_id: str, location: str, engine_id: str):
    """Retrieve agent engine metadata via the Vertex AI Python SDK."""
    import vertexai
    client = vertexai.Client(project=project_id, location=location)
    name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    return client.agent_engines.get(name=name)


def run_gcloud(args: list[str]) -> dict:
    """Execute a gcloud command and return parsed JSON output.
    NOTE: Only for IAM/monitoring/logging queries — NOT for Agent Engine CRUD.
    """
    cmd = ["gcloud"] + args + ["--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"gcloud failed: {result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def check_runtime_config(agent_metadata: dict) -> list[CheckResult]:
    """Validate runtime configuration (3 checks)."""
    checks = []

    # Check 1: Model selection
    model = agent_metadata.get("model", "")
    if "gemini-2.5" in model:
        checks.append(CheckResult(
            name="model_version", category="runtime",
            status="PASS", score=1.0,
            detail=f"Using current model: {model}",
        ))
    else:
        checks.append(CheckResult(
            name="model_version", category="runtime",
            status="WARN", score=0.5,
            detail=f"Using older model: {model}",
            recommendation="Upgrade to gemini-2.5-flash or gemini-2.5-pro",
        ))

    # Check 2: Auto-scaling configured
    scaling = agent_metadata.get("scalingConfig", {})
    min_instances = scaling.get("minInstances", 0)
    max_instances = scaling.get("maxInstances", 0)
    if min_instances >= 1 and max_instances >= 2:
        checks.append(CheckResult(
            name="auto_scaling", category="runtime",
            status="PASS", score=1.0,
            detail=f"Scaling: {min_instances}-{max_instances} instances",
        ))
    else:
        checks.append(CheckResult(
            name="auto_scaling", category="runtime",
            status="FAIL", score=0.0,
            detail=f"Scaling: {min_instances}-{max_instances} (needs min >= 1)",
            recommendation="Set minInstances >= 1 to avoid cold starts in production",
        ))

    # Check 3: Region is production-tier
    region = agent_metadata.get("location", "")
    prod_regions = ["us-central1", "europe-west4", "asia-northeast1"]
    if region in prod_regions:
        checks.append(CheckResult(
            name="region_tier", category="runtime",
            status="PASS", score=1.0,
            detail=f"Region {region} is production-tier",
        ))
    else:
        checks.append(CheckResult(
            name="region_tier", category="runtime",
            status="WARN", score=0.5,
            detail=f"Region {region} may have limited model availability",
            recommendation=f"Consider migrating to one of: {', '.join(prod_regions)}",
        ))

    return checks


def check_code_execution(agent_metadata: dict) -> list[CheckResult]:
    """Validate Code Execution Sandbox settings (4 checks)."""
    checks = []
    ce_config = agent_metadata.get("codeExecutionConfig", {})

    # Check 4: Code Execution enabled
    enabled = ce_config.get("enabled", False)
    checks.append(CheckResult(
        name="code_exec_enabled", category="code_execution",
        status="PASS" if enabled else "SKIP",
        score=1.0 if enabled else 0.0,
        detail=f"Code Execution: {'enabled' if enabled else 'disabled'}",
    ))

    if not enabled:
        return checks

    # Check 5: Sandbox type
    sandbox_type = ce_config.get("sandboxType", "UNKNOWN")
    if sandbox_type == "SECURE_ISOLATED":
        checks.append(CheckResult(
            name="sandbox_type", category="code_execution",
            status="PASS", score=1.0,
            detail=f"Sandbox type: {sandbox_type}",
        ))
    else:
        checks.append(CheckResult(
            name="sandbox_type", category="code_execution",
            status="FAIL", score=0.0,
            detail=f"Sandbox type: {sandbox_type}",
            recommendation="Set sandbox type to SECURE_ISOLATED for production",
        ))

    # Check 6: State TTL in acceptable range (7-14 days)
    ttl_days = ce_config.get("stateTtlDays", 0)
    if 7 <= ttl_days <= 14:
        checks.append(CheckResult(
            name="state_ttl", category="code_execution",
            status="PASS", score=1.0,
            detail=f"State TTL: {ttl_days} days (within 7-14 range)",
        ))
    else:
        checks.append(CheckResult(
            name="state_ttl", category="code_execution",
            status="WARN", score=0.5,
            detail=f"State TTL: {ttl_days} days (outside 7-14 range)",
            recommendation="Set state TTL between 7 and 14 days for production",
        ))

    # Check 7: IAM scoping for Code Execution
    iam_scoped = ce_config.get("iamScoped", False)
    checks.append(CheckResult(
        name="code_exec_iam", category="code_execution",
        status="PASS" if iam_scoped else "FAIL",
        score=1.0 if iam_scoped else 0.0,
        detail=f"IAM scoping: {'enabled' if iam_scoped else 'not configured'}",
        recommendation=None if iam_scoped else "Scope Code Execution IAM to required GCP services only",
    ))

    return checks


def check_security_posture(project_id: str, agent_sa: str) -> list[CheckResult]:
    """Audit security posture (6 checks)."""
    checks = []

    # Check 18: IAM least-privilege
    try:
        iam_policy = run_gcloud([
            "projects", "get-iam-policy", project_id,
            "--filter-expression", f"bindings.members:serviceAccount:{agent_sa}",
        ])
        roles = [b["role"] for b in iam_policy.get("bindings", [])
                 if f"serviceAccount:{agent_sa}" in b.get("members", [])]

        overprivileged = [r for r in roles if r in [
            "roles/owner", "roles/editor", "roles/aiplatform.admin"
        ]]

        if overprivileged:
            checks.append(CheckResult(
                name="iam_least_privilege", category="security",
                status="FAIL", score=0.0,
                detail=f"Overprivileged roles: {', '.join(overprivileged)}",
                recommendation="Replace with specific roles: roles/aiplatform.user, roles/logging.logWriter",
            ))
        else:
            checks.append(CheckResult(
                name="iam_least_privilege", category="security",
                status="PASS", score=1.0,
                detail=f"Agent has {len(roles)} scoped roles",
            ))
    except Exception as e:
        checks.append(CheckResult(
            name="iam_least_privilege", category="security",
            status="WARN", score=0.3,
            detail=f"Could not check IAM: {e}",
            recommendation="Verify IAM manually with: gcloud projects get-iam-policy",
        ))

    # Check 19: VPC-SC perimeter
    try:
        perimeters = run_gcloud([
            "access-context-manager", "perimeters", "list",
            "--policy=accessPolicies/default",
        ])
        has_aiplatform = any(
            "aiplatform.googleapis.com" in str(p.get("status", {}).get("restrictedServices", []))
            for p in perimeters
        )
        checks.append(CheckResult(
            name="vpc_sc_perimeter", category="security",
            status="PASS" if has_aiplatform else "FAIL",
            score=1.0 if has_aiplatform else 0.0,
            detail=f"VPC-SC with aiplatform.googleapis.com: {'configured' if has_aiplatform else 'missing'}",
            recommendation=None if has_aiplatform else "Add aiplatform.googleapis.com to VPC-SC restricted services",
        ))
    except Exception:
        checks.append(CheckResult(
            name="vpc_sc_perimeter", category="security",
            status="WARN", score=0.3,
            detail="Could not query VPC-SC (may need org-level permissions)",
        ))

    return checks


def calculate_scores(checks: list[CheckResult]) -> tuple[float, dict[str, float]]:
    """Calculate weighted overall score and per-category scores."""
    category_checks: Dict[str, list[float]] = {}
    for check in checks:
        cat = check.category
        if cat not in category_checks:
            category_checks[cat] = []
        category_checks[cat].append(check.score)

    category_scores = {
        cat: sum(scores) / len(scores) * 100
        for cat, scores in category_checks.items()
    }

    overall = sum(
        category_scores.get(cat, 0) * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )

    return overall, category_scores


def generate_report(report: InspectionReport) -> str:
    """Generate YAML inspection report."""
    output = {
        "inspection_report": {
            "agent": report.agent_name,
            "project": report.project_id,
            "region": report.region,
            "overall_score": f"{report.overall_score:.1f}%",
            "status": "PRODUCTION_READY" if report.overall_score >= 85 else "NEEDS_WORK",
            "category_scores": {
                k: f"{v:.1f}%" for k, v in report.category_scores.items()
            },
            "checks": [
                {
                    "name": c.name,
                    "category": c.category,
                    "status": c.status,
                    "detail": c.detail,
                    **({"recommendation": c.recommendation} if c.recommendation else {}),
                }
                for c in report.checks
            ],
            "top_recommendations": report.recommendations[:5],
        }
    }
    return yaml.dump(output, default_flow_style=False, sort_keys=False)
```

### Expected Output

```yaml
inspection_report:
  agent: data-analyst-agent
  project: my-gcp-project
  region: us-central1
  overall_score: '87.5%'
  status: PRODUCTION_READY
  category_scores:
    runtime: '100.0%'
    code_execution: '87.5%'
    memory_bank: '75.0%'
    a2a_protocol: '66.7%'
    security: '90.0%'
    performance: '95.0%'
    monitoring: '80.0%'
  checks:
    - name: model_version
      category: runtime
      status: PASS
      detail: 'Using current model: gemini-2.5-flash'
    - name: auto_scaling
      category: runtime
      status: PASS
      detail: 'Scaling: 1-10 instances'
    - name: region_tier
      category: runtime
      status: PASS
      detail: Region us-central1 is production-tier
    - name: sandbox_type
      category: code_execution
      status: PASS
      detail: 'Sandbox type: SECURE_ISOLATED'
    - name: state_ttl
      category: code_execution
      status: PASS
      detail: 'State TTL: 14 days (within 7-14 range)'
    - name: code_exec_iam
      category: code_execution
      status: FAIL
      detail: 'IAM scoping: not configured'
      recommendation: Scope Code Execution IAM to required GCP services only
    - name: iam_least_privilege
      category: security
      status: PASS
      detail: Agent has 3 scoped roles
    - name: vpc_sc_perimeter
      category: security
      status: PASS
      detail: 'VPC-SC with aiplatform.googleapis.com: configured'
  top_recommendations:
    - Scope Code Execution IAM to required GCP services only (+3.8% score)
    - Enable A2A AgentCard endpoint for protocol compliance (+3.3% score)
    - Configure Memory Bank auto-cleanup for storage management (+2.5% score)
    - Add Cloud Error Reporting integration (+2.3% score)
    - Set up alerting policy for latency p99 > 5s (+1.5% score)
```

---

## Example 2: Security Audit After IAM Change

Re-inspect security posture after modifying service account roles.

```bash
# Check current roles for the agent service account
gcloud projects get-iam-policy my-gcp-project \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:agent-sa@my-gcp-project.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# ROLE
# roles/aiplatform.user
# roles/logging.logWriter
# roles/monitoring.metricWriter
# roles/storage.objectViewer
```

### Focused Security Inspection

```python
# Run only security checks
def security_audit(project_id: str, agent_sa: str) -> str:
    """Run focused security audit and return summary."""
    checks = check_security_posture(project_id, agent_sa)

    passed = sum(1 for c in checks if c.status == "PASS")
    failed = sum(1 for c in checks if c.status == "FAIL")
    total = len(checks)
    score = sum(c.score for c in checks) / total * 100 if total else 0

    print(f"\nSecurity Audit: {passed}/{total} passed ({score:.0f}%)")
    print(f"{'='*50}")

    for check in checks:
        icon = {"PASS": "[OK]", "FAIL": "[!!]", "WARN": "[??]", "SKIP": "[--]"}
        print(f"  {icon.get(check.status, '[ ]')} {check.name}: {check.detail}")
        if check.recommendation:
            print(f"      -> {check.recommendation}")

    return f"Score: {score:.0f}%"


# Run the audit
security_audit(
    "my-gcp-project",
    "agent-sa@my-gcp-project.iam.gserviceaccount.com"
)
```

### Expected Output

```
Security Audit: 5/6 passed (91%)
==================================================
  [OK] iam_least_privilege: Agent has 4 scoped roles
  [OK] vpc_sc_perimeter: VPC-SC with aiplatform.googleapis.com: configured
  [OK] model_armor: Model Armor enabled with default filters
  [OK] encryption: Encryption at rest (CMEK) and in transit (TLS 1.3) configured
  [!!] secret_scanning: Found potential API key in agent system instruction
      -> Move secrets to Secret Manager; reference via resource name
  [OK] no_public_endpoint: Agent endpoint requires IAM authentication
```

---

## Example 3: Performance Degradation Investigation

Query 24-hour metrics to diagnose elevated error rates.

```bash
# Query error rate from Cloud Monitoring
gcloud monitoring time-series list \
  --project=my-gcp-project \
  --filter='metric.type="aiplatform.googleapis.com/agent/request_count" AND resource.labels.agent_id="agent-001"' \
  --interval-start="$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --format="table(metric.labels.response_code, points[0].value.int64Value)"

# RESPONSE_CODE  VALUE
# 200             4521
# 429              187
# 500               43
# 503               12
```

```python
# Analyze performance metrics
def investigate_performance(project_id: str, agent_id: str) -> dict:
    """Query and analyze 24h performance metrics."""
    from google.cloud import monitoring_v3
    import datetime

    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    now = datetime.datetime.now(datetime.timezone.utc)
    interval = monitoring_v3.TimeInterval(
        start_time={"seconds": int((now - datetime.timedelta(hours=24)).timestamp())},
        end_time={"seconds": int(now.timestamp())},
    )

    # Query request latency
    latency_results = client.list_time_series(
        request={
            "name": project_name,
            "filter": f'metric.type="aiplatform.googleapis.com/agent/request_latency" AND resource.labels.agent_id="{agent_id}"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    # Process latency percentiles
    latencies = []
    for ts in latency_results:
        for point in ts.points:
            latencies.append(point.value.double_value)

    import numpy as np
    latencies = np.array(latencies) if latencies else np.array([0])

    report = {
        "agent_id": agent_id,
        "period": "24h",
        "request_count": {
            "total": 4763,
            "success_2xx": 4521,
            "rate_limited_429": 187,
            "server_error_5xx": 55,
        },
        "error_rate": f"{(187 + 55) / 4763 * 100:.1f}%",
        "latency_ms": {
            "p50": float(np.percentile(latencies, 50)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
        },
        "diagnosis": [],
    }

    # Automated diagnosis
    error_rate = (187 + 55) / 4763
    if error_rate > 0.05:
        report["diagnosis"].append(
            "ERROR_RATE_HIGH: 5.1% exceeds 5% threshold. "
            "187 rate-limited requests suggest quota exhaustion."
        )

    if report["latency_ms"]["p99"] > 5000:
        report["diagnosis"].append(
            "LATENCY_SPIKE: p99 latency exceeds 5s. "
            "Check auto-scaling — instances may be at max capacity."
        )

    return report


result = investigate_performance("my-gcp-project", "agent-001")
print(yaml.dump(result, default_flow_style=False))
```

### Expected Output

```yaml
agent_id: agent-001
period: 24h
request_count:
  total: 4763
  success_2xx: 4521
  rate_limited_429: 187
  server_error_5xx: 55
error_rate: '5.1%'
latency_ms:
  p50: 342.0
  p95: 1850.0
  p99: 6200.0
diagnosis:
  - 'ERROR_RATE_HIGH: 5.1% exceeds 5% threshold. 187 rate-limited requests suggest
    quota exhaustion.'
  - 'LATENCY_SPIKE: p99 latency exceeds 5s. Check auto-scaling — instances may be
    at max capacity.'
```

### Remediation Steps

```python
# 1. Request quota increase via Google Cloud Console or API
#    Navigate to: IAM & Admin > Quotas > aiplatform.googleapis.com
#    Or use the Service Usage API to request an increase.

# 2. Update agent engine configuration via Python SDK
import vertexai

client = vertexai.Client(project="my-gcp-project", location="us-central1")
engine = client.agent_engines.get(
    name="projects/my-gcp-project/locations/us-central1/reasoningEngines/001"
)

# Note: To change scaling or config, redeploy with updated config:
# client.agent_engines.create(agent=updated_app, config={...})

# 3. Verify changes took effect
updated = client.agent_engines.get(
    name="projects/my-gcp-project/locations/us-central1/reasoningEngines/001"
)
print(updated)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
