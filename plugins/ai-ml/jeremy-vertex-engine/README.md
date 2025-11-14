# Jeremy Vertex Engine

**🎯 VERTEX AI AGENT ENGINE DEPLOYMENT ONLY**

Expert inspector and orchestrator for **Vertex AI Agent Engine** - Google Cloud's fully-managed, serverless agent runtime platform.

## ⚠️ Important: What This Plugin Is For

**✅ THIS PLUGIN IS FOR:**
- **Vertex AI Agent Engine** deployments (fully-managed runtime)
- **ADK (Agent Development Kit)** agents deployed to Agent Engine
- **Reasoning Engine API** resources (`google_vertex_ai_reasoning_engine`)
- Agent Engine features: Memory Bank, Code Execution Sandbox, Sessions, A2A Protocol

**❌ THIS PLUGIN IS NOT FOR:**
- Cloud Run deployments (use `jeremy-genkit-terraform` or `jeremy-adk-terraform` with `--cloud-run` flag)
- LangChain/LlamaIndex on other platforms
- Self-hosted agent infrastructure
- Cloud Functions or other serverless platforms

## Overview

This plugin provides comprehensive inspection and validation capabilities for agents deployed to the **Vertex AI Agent Engine managed runtime**. It acts as a quality assurance layer ensuring agents are properly configured, secure, performant, and production-ready on Google's fully-managed agent infrastructure.

## Installation

```bash
/plugin install jeremy-vertex-engine@claude-code-plugins-plus
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
# Minimum required roles for inspection:
- roles/aiplatform.user              # Query Agent Engine resources
- roles/discoveryengine.viewer       # View agent configurations
- roles/logging.viewer               # Read agent logs
- roles/monitoring.viewer            # Access metrics
- roles/cloudtrace.user              # View trace data
```

### Required Python Packages

**Install via pip:**
```bash
# Core Vertex AI SDK (with Agent Engine support)
pip install google-cloud-aiplatform[agent_engines]>=1.120.0

# ADK SDK (if building ADK agents)
pip install google-adk>=1.15.1

# Observability & Monitoring
pip install google-cloud-logging>=3.10.0
pip install google-cloud-monitoring>=2.21.0
pip install google-cloud-trace>=1.13.0

# Optional: A2A Protocol SDK
pip install a2a-sdk>=0.3.4
```

**All dependencies at once:**
```bash
pip install --upgrade \
    'google-cloud-aiplatform[agent_engines]>=1.120.0' \
    'google-adk>=1.15.1' \
    'google-cloud-logging>=3.10.0' \
    'google-cloud-monitoring>=2.21.0' \
    'google-cloud-trace>=1.13.0' \
    'a2a-sdk>=0.3.4'
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
```

**Verify Installation:**
```bash
gcloud --version
# Should show: Google Cloud SDK 450.0.0+ (or higher)

# Test Agent Engine access
gcloud alpha ai agent-engines list --location=us-central1 --project=YOUR_PROJECT_ID
```

### Vertex AI Agent Engine Requirements

**This plugin works with agents deployed via:**

1. **ADK Deployment to Agent Engine:**
```python
from google.cloud import aiplatform

client = aiplatform.Client(project=PROJECT_ID, location=LOCATION)

# Deploy ADK agent to Agent Engine
agent_engine = client.agent_engines.create(
    config={
        "display_name": "my-adk-agent",
        "agent_framework": "google-adk"  # ← Required for ADK
    }
)
```

2. **Terraform Deployment:**
```hcl
resource "google_vertex_ai_reasoning_engine" "agent" {
  display_name = "my-agent"
  region       = "us-central1"

  spec {
    agent_framework = "google-adk"  # ← ADK agents
    # OR omit for custom agents

    package_spec {
      pickle_object_gcs_uri    = "gs://bucket/agent.pkl"
      python_version           = "3.12"
      requirements_gcs_uri     = "gs://bucket/requirements.txt"
    }
  }
}
```

3. **Direct SDK Deployment:**
```python
# Custom agent template (NOT LangChain)
from vertexai.preview.reasoning_engines import ReasoningEngine

agent = ReasoningEngine.create(
    my_agent_instance,
    requirements=["google-cloud-aiplatform[agent_engines]>=1.120.0"],
    display_name="custom-agent"
)
```

### ❌ NOT Compatible With

- **Cloud Run deployments** (different runtime, use Cloud Run monitoring tools)
- **LangChain on non-Agent Engine platforms** (use LangSmith/LangFuse)
- **LlamaIndex custom servers** (not Agent Engine)
- **Self-hosted agent infrastructure** (requires custom monitoring)

## Features

✅ **Runtime Configuration Inspection**: Validate model, tools, VPC settings
✅ **Code Execution Sandbox Validation**: Check security, state persistence, IAM
✅ **Memory Bank Configuration**: Verify retention, indexing, query performance
✅ **A2A Protocol Compliance**: Ensure AgentCard and API endpoints functional
✅ **Security Audits**: IAM, VPC-SC, encryption, Model Armor checks
✅ **Performance Monitoring**: Latency, error rates, token usage, costs
✅ **Production Readiness Scoring**: Comprehensive 28-point checklist
✅ **Health Monitoring**: Real-time metrics and alerting

## Components

### Agent
- **vertex-engine-inspector**: Comprehensive agent inspector with validation logic

### Skills (Auto-Activating)
- **vertex-engine-inspector**: Triggers on "inspect agent engine", "validate deployment"
  - **Tool Permissions**: Read, Grep, Glob, Bash (read-only)
  - **Version**: 1.0.0 (2025 schema compliant)

## Quick Start

### Natural Language Activation

Simply mention what you need:

```
"Inspect my Vertex AI Engine agent deployment"
"Validate the Code Execution Sandbox configuration"
"Check Memory Bank settings for my agent"
"Monitor agent health over the last 24 hours"
"Production readiness check for agent-id-123"
```

The skill auto-activates and performs comprehensive inspection.

### What Gets Inspected

1. **Runtime Configuration**
   - Model selection and settings
   - Enabled tools (Code Execution, Memory Bank)
   - VPC and networking configuration
   - Resource allocation and scaling

2. **Code Execution Sandbox**
   - Security isolation validation
   - State persistence TTL (1-14 days)
   - IAM least privilege verification
   - Performance settings

3. **Memory Bank**
   - Persistent memory configuration
   - Retention policies
   - Query performance (indexing, caching)
   - Storage backend validation

4. **A2A Protocol**
   - AgentCard availability and structure
   - Task API functionality
   - Status API accessibility
   - Protocol version compliance

5. **Security Posture**
   - IAM roles and permissions
   - VPC Service Controls
   - Model Armor (prompt injection protection)
   - Encryption at rest and in transit

6. **Performance Metrics**
   - Error rates and latency
   - Token usage and costs
   - Throughput and scaling
   - SLO compliance

7. **Production Readiness**
   - 28-point comprehensive checklist
   - Weighted scoring across 5 categories
   - Overall readiness status
   - Actionable recommendations

## Production Readiness Score

The plugin generates a production readiness score based on:

- **Security** (30%): 6 checks
- **Performance** (25%): 6 checks
- **Monitoring** (20%): 6 checks
- **Compliance** (15%): 5 checks
- **Reliability** (10%): 5 checks

### Status Levels

🟢 **PRODUCTION READY (85-100%)**: Safe to deploy
🟡 **NEEDS IMPROVEMENT (70-84%)**: Address issues first
🔴 **NOT READY (<70%)**: Critical failures present

## Integration with Other Plugins

### jeremy-adk-orchestrator
- Orchestrator deploys → Inspector validates
- Continuous feedback loop

### jeremy-vertex-validator
- Validator checks code → Inspector checks runtime
- Pre/post deployment validation

### jeremy-adk-terraform
- Terraform provisions → Inspector validates
- Infrastructure verification

## Use Cases

### Pre-Production Validation
Before deploying to production:
```
"Run production readiness check on staging agent"
```

### Post-Deployment Verification
After deployment:
```
"Validate agent-xyz deployment was successful"
```

### Ongoing Health Monitoring
Regular health checks:
```
"Monitor agent health for the last 7 days"
```

### Security Audits
Compliance validation:
```
"Perform security audit on production agents"
```

### Troubleshooting
When issues occur:
```
"Why is my agent responding slowly?"
"Investigate high error rate on agent-abc"
```

## Example Inspection Report

```
Agent: gcp-deployer-agent
Status: 🟢 PRODUCTION READY (87%)

✅ Code Execution: Enabled (TTL: 14 days)
✅ Memory Bank: Enabled (retention: 90 days)
✅ A2A Protocol: Fully compliant
✅ Security: 92% score
✅ Performance: Error rate 2.3%, Latency 1.8s (p95)

⚠️ Recommendations:
1. Enable multi-region deployment
2. Configure automated backups
3. Add circuit breaker pattern
```

## Observability & Monitoring

### Agent Engine Observability Dashboard

**New in 2025**: Vertex AI Agent Engine provides a built-in observability dashboard for monitoring agent performance.

**Access the Dashboard:**
```bash
# Navigate to Cloud Console
https://console.cloud.google.com/vertex-ai/agent-engines/[AGENT_ENGINE_ID]/observability?project=[PROJECT_ID]
```

**Key Metrics Available:**
- **Request Volume**: Total queries processed over time
- **Latency Distribution**: p50, p90, p95, p99 response times
- **Error Rates**: Failed requests, timeout errors, model errors
- **Token Usage**: Input/output tokens, cost estimation
- **Memory Bank Operations**: Query latency, cache hit rate
- **Code Execution Stats**: Sandbox invocations, execution time

### Cloud Trace Integration

**Enable distributed tracing with OpenTelemetry:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from google.cloud import aiplatform

# Configure Cloud Trace exporter
trace.set_tracer_provider(TracerProvider())
cloud_trace_exporter = CloudTraceSpanExporter()
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)

tracer = trace.get_tracer(__name__)

# Instrument agent queries
with tracer.start_as_current_span("agent_query") as span:
    span.set_attribute("agent.id", agent_engine_id)
    span.set_attribute("user.query", user_query)

    response = agent.query(user_query)

    span.set_attribute("response.tokens", response.token_count)
    span.set_attribute("response.latency_ms", response.latency)
```

**View traces in Cloud Console:**
```bash
# Navigate to Trace Explorer
https://console.cloud.google.com/traces/list?project=[PROJECT_ID]

# Filter by agent queries
resource.type="aiplatform.googleapis.com/Agent"
```

### Cloud Logging

**Query agent logs using Cloud Logging:**

```python
from google.cloud import logging

client = logging.Client(project=PROJECT_ID)

# Get agent logs from the last 24 hours
filter_str = f'''
resource.type="aiplatform.googleapis.com/Agent"
resource.labels.agent_id="{agent_engine_id}"
timestamp>="2025-01-12T00:00:00Z"
severity>="WARNING"
'''

for entry in client.list_entries(filter_=filter_str, page_size=100):
    print(f"{entry.timestamp}: {entry.payload}")
```

**Common log queries:**

```bash
# View all agent errors
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent AND severity>=ERROR" \
    --project=[PROJECT_ID] \
    --limit=50 \
    --format=json

# Memory Bank query performance
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent AND jsonPayload.component=memory_bank" \
    --project=[PROJECT_ID] \
    --limit=100

# Code Execution Sandbox logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent AND jsonPayload.component=code_execution" \
    --project=[PROJECT_ID] \
    --limit=100
```

### Cloud Monitoring Custom Metrics

**Create custom dashboards for agent monitoring:**

```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{PROJECT_ID}"

# Query agent latency metric
interval = monitoring_v3.TimeInterval(
    {
        "end_time": {"seconds": int(time.time())},
        "start_time": {"seconds": int(time.time() - 3600)},
    }
)

results = client.list_time_series(
    request={
        "name": project_name,
        "filter": 'metric.type="aiplatform.googleapis.com/agent/prediction_latencies"',
        "interval": interval,
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    }
)

for result in results:
    print(f"Agent: {result.resource.labels['agent_id']}")
    for point in result.points:
        print(f"  Latency: {point.value.distribution_value.mean}ms")
```

### Alerting Policies

**Create alerts for agent health issues:**

```python
from google.cloud import monitoring_v3

# Alert on high error rate
alert_policy = monitoring_v3.AlertPolicy(
    display_name="Agent High Error Rate",
    conditions=[
        monitoring_v3.AlertPolicy.Condition(
            display_name="Error rate > 5%",
            condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                filter='metric.type="aiplatform.googleapis.com/agent/error_count"',
                comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                threshold_value=0.05,
                duration={"seconds": 300},
            ),
        )
    ],
    notification_channels=[notification_channel_id],
    alert_strategy=monitoring_v3.AlertPolicy.AlertStrategy(
        auto_close={"seconds": 86400}
    ),
)

policy_client = monitoring_v3.AlertPolicyServiceClient()
policy = policy_client.create_alert_policy(
    name=f"projects/{PROJECT_ID}",
    alert_policy=alert_policy,
)
```

**Common alert conditions:**
- Error rate exceeds 5% for 5 minutes
- p95 latency exceeds 10 seconds
- Memory Bank cache hit rate drops below 60%
- Code Execution Sandbox timeout rate exceeds 2%
- Token usage exceeds budget threshold

## Storage Integration

### BigQuery Connector

**New in 2025**: Export agent logs and analytics to BigQuery for long-term analysis.

**Setup BigQuery Export:**

```python
from google.cloud import aiplatform

# Configure BigQuery connector for agent logs
connector_config = {
    "bigquery_destination": {
        "output_uri": f"bq://{PROJECT_ID}.agent_analytics.agent_logs"
    },
    "export_interval_hours": 1,  # Export every hour
    "log_types": [
        "AGENT_QUERIES",
        "MEMORY_BANK_OPERATIONS",
        "CODE_EXECUTION_EVENTS",
        "A2A_PROTOCOL_CALLS"
    ]
}

client = aiplatform.gapic.ReasoningEngineServiceClient()
connector = client.create_data_connector(
    parent=f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_engine_id}",
    data_connector=connector_config
)
```

**Query agent analytics in BigQuery:**

```sql
-- Agent query volume and latency trends
SELECT
  DATE(timestamp) as query_date,
  COUNT(*) as total_queries,
  AVG(latency_ms) as avg_latency,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] as p95_latency,
  SUM(error_count) as total_errors
FROM `project.agent_analytics.agent_logs`
WHERE agent_id = 'your-agent-id'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY query_date
ORDER BY query_date DESC;

-- Memory Bank cache performance
SELECT
  memory_bank_id,
  COUNT(*) as total_queries,
  SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) / COUNT(*) as cache_hit_rate,
  AVG(query_latency_ms) as avg_query_latency
FROM `project.agent_analytics.agent_logs`
WHERE component = 'MEMORY_BANK'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY memory_bank_id;

-- Token usage and cost analysis
SELECT
  DATE(timestamp) as usage_date,
  SUM(input_tokens) as total_input_tokens,
  SUM(output_tokens) as total_output_tokens,
  SUM(input_tokens + output_tokens) as total_tokens,
  SUM((input_tokens * 0.00025 + output_tokens * 0.00075) / 1000) as estimated_cost_usd
FROM `project.agent_analytics.agent_logs`
WHERE agent_id = 'your-agent-id'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY usage_date
ORDER BY usage_date DESC;
```

**Create scheduled reports:**

```bash
# Create BigQuery scheduled query
bq query \
  --use_legacy_sql=false \
  --destination_table=agent_analytics.daily_summary \
  --replace \
  --schedule='every 24 hours' \
  --display_name='Agent Daily Summary' \
  'SELECT
     DATE(timestamp) as report_date,
     agent_id,
     COUNT(*) as total_queries,
     AVG(latency_ms) as avg_latency,
     SUM(error_count) as total_errors,
     SUM(input_tokens + output_tokens) as total_tokens
   FROM `project.agent_analytics.agent_logs`
   WHERE timestamp >= CURRENT_DATE()
   GROUP BY report_date, agent_id'
```

### Cloud Storage Integration

**Store agent artifacts and code execution outputs:**

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(f"{PROJECT_ID}-agent-artifacts")

# Configure Code Execution Sandbox to save artifacts
sandbox_config = {
    "artifact_storage": {
        "gcs_bucket": bucket.name,
        "retention_days": 30,
        "export_patterns": ["*.png", "*.csv", "*.json", "*.log"]
    }
}

# Retrieve execution artifacts
def get_execution_artifacts(execution_id: str):
    """Download artifacts from a code execution run."""
    prefix = f"executions/{execution_id}/"
    blobs = bucket.list_blobs(prefix=prefix)

    artifacts = []
    for blob in blobs:
        local_path = f"/tmp/{blob.name.split('/')[-1]}"
        blob.download_to_filename(local_path)
        artifacts.append(local_path)

    return artifacts
```

**Incremental refresh for large datasets:**

```python
# Configure incremental data export (new in 2025)
from google.cloud import discoveryengine_v1

# For Memory Bank with large knowledge bases
data_store_config = {
    "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/dataStores/{DATA_STORE_ID}",
    "content_config": "CONTENT_REQUIRED",
    "document_processing_config": {
        "chunking_config": {
            "layout_based_chunking_config": {
                "chunk_size": 500,
                "include_ancestor_headings": True
            }
        }
    },
    "starting_schema": {
        "incremental_updates": {
            "gcs_source": f"gs://{bucket.name}/knowledge-base/",
            "sync_interval_hours": 4,
            "change_detection": "TIMESTAMP"  # Only sync modified files
        }
    }
}
```

**Monitor storage costs:**

```bash
# Check agent storage usage
gsutil du -sh gs://[PROJECT_ID]-agent-artifacts/

# List large artifacts
gsutil ls -lh gs://[PROJECT_ID]-agent-artifacts/** | sort -k1 -h -r | head -20

# Set lifecycle policy to auto-delete old artifacts
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["executions/", "logs/"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://[PROJECT_ID]-agent-artifacts/
```

### Data Export Patterns

**Common data export schedules for different use cases:**

| Use Case | Export Frequency | Destination | Retention |
|----------|-----------------|-------------|-----------|
| Real-time monitoring | Streaming | Cloud Logging | 30 days |
| Daily analytics | Every 24 hours | BigQuery | 1 year |
| Compliance audit | Weekly | Cloud Storage (archive) | 7 years |
| Cost analysis | Monthly | BigQuery | Indefinite |
| Debugging logs | On-demand | Cloud Storage | 90 days |

**Example: Weekly compliance export**

```python
from google.cloud import aiplatform
import datetime

def export_compliance_logs():
    """Export agent logs for compliance audit."""
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=7)

    export_config = {
        "gcs_destination": {
            "output_uri_prefix": f"gs://{PROJECT_ID}-compliance/agents/{start_time.strftime('%Y-%m-%d')}/"
        },
        "time_range": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        "log_filters": [
            "severity>=WARNING",  # All warnings and errors
            "jsonPayload.user_pii_accessed=true",  # PII access logs
            "jsonPayload.model_armor_triggered=true"  # Security events
        ]
    }

    client = aiplatform.gapic.ReasoningEngineServiceClient()
    operation = client.export_logs(
        parent=f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_engine_id}",
        export_config=export_config
    )

    print(f"Compliance export started: {operation.name}")
    return operation

# Schedule with Cloud Scheduler
# gcloud scheduler jobs create http compliance-export \
#   --schedule="0 0 * * 0" \
#   --uri="https://[REGION]-[PROJECT_ID].cloudfunctions.net/export-compliance-logs" \
#   --http-method=POST
```

## Requirements

- Google Cloud Project with Vertex AI enabled
- Deployed agents on Agent Engine
- Appropriate IAM permissions for inspection
- Cloud Monitoring enabled
- Cloud Logging enabled (for observability features)
- BigQuery dataset (for analytics integration)

## License

MIT

## Support

- Issues: https://github.com/jeremylongshore/claude-code-plugins/issues
- Discussions: https://github.com/jeremylongshore/claude-code-plugins/discussions

## Version

1.0.0 (2025) - Agent Engine GA support with comprehensive inspection capabilities
