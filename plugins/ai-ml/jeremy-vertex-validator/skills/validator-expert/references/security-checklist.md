# Security Validation Checklist (30% Weight)

Sources:

- Vertex AI Security Best Practices
- [Agent Identity for Agent Engine](https://cloud.google.com/agent-builder/agent-engine/agent-identity)
- [Managing Access for Deployed Agents](https://cloud.google.com/agent-builder/agent-engine/manage/access)
- [IAM Roles for Vertex AI](https://cloud.google.com/iam/docs/roles-permissions/aiplatform)

---

## Agent Identity (Recommended — 2025+)

Agent Identity is a first-class IAM principal tied to agent lifecycle. Replaces service-account-only model for new deployments.

**Check for:**

- Agent Identity enabled (preferred over service accounts for new deployments)
- Certificate-bound tokens with Context-Aware Access (CAA) + mTLS enforced
- Credentials are un-replayable outside their Cloud Run container
- Agent identity auto-destroyed when agent is deleted

**Recommended roles for Agent Identity:**

| Role | Purpose |
|------|---------|
| `roles/aiplatform.expressUser` | Inference, sessions, memory access |
| `roles/serviceusage.serviceUsageConsumer` | Quota and SDK usage |
| `roles/browser` | Basic Cloud functionalities |

**Anti-patterns:**

- Using `roles/aiplatform.admin` on agent identity (too broad)
- Using `roles/aiplatform.user` when `expressUser` suffices
- Opting out of CAA/mTLS verification

Source: [Agent Identity](https://cloud.google.com/agent-builder/agent-engine/agent-identity)

---

## IAM & Access Control (Service Account Pattern)

For legacy or cross-project deployments using service accounts:

- Service accounts follow least privilege principle
- No overly permissive roles (`roles/owner`, `roles/editor`, `roles/aiplatform.admin`)
- Workload Identity Federation configured (no static keys)
- No hardcoded credentials in code or env vars
- Default agent SA: `service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`
- Default role: `roles/aiplatform.reasoningEngineServiceAgent`
- Cross-project: `roles/iam.serviceAccountTokenCreator` granted to Vertex AI Service Agent

**Least privilege custom role permissions (prediction-only agent):**

```
aiplatform.endpoints.predict
aiplatform.sessions.create
aiplatform.sessions.get
aiplatform.sessions.update
aiplatform.memories.retrieve
aiplatform.memories.generate
serviceusage.quotas.get
```

### Validation Commands

```bash
# List service account bindings
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.members)" \
  --filter="bindings.members:serviceAccount"

# Check for overly permissive roles
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:(roles/owner OR roles/editor OR roles/aiplatform.admin)"
```

```python
# Check agent identity status (no gcloud CLI — use Python SDK)
import vertexai
client = vertexai.Client(project="PROJECT_ID", location="LOCATION")
remote_agent = client.agent_engines.get(
    name="projects/PROJECT_ID/locations/LOCATION/reasoningEngines/AGENT_ID"
)
print(remote_agent)  # Inspect agent identity configuration
```

Source: [Custom Service Accounts](https://cloud.google.com/vertex-ai/docs/general/custom-service-account)

---

## Memory Bank IAM Conditions

For multi-tenant agents, use IAM Conditions to scope memory access per user/group:

- IAM Conditions with `aiplatform.googleapis.com/memoryScope` attribute
- Restrict memory operations to specific user/group scopes
- Limitation: `ListMemories` and `PurgeMemories` need unconditional grants

```yaml
# Example IAM Condition
expression: 'api.getAttribute("aiplatform.googleapis.com/memoryScope", "").startsWith("user-")'
title: "User-scoped memory access"
```

Source: [Memory Bank IAM Conditions](https://cloud.google.com/agent-builder/agent-engine/memory-bank/iam-conditions)

---

## Model Armor

- Model Armor enabled for all ADK-based agents (GA with `gcloud model-armor` command group)
- Agent needs `roles/modelarmor.user` for sanitize APIs
- Templates managed via `roles/modelarmor.admin`
- Org-level floor settings via `roles/modelarmor.floorSettingsAdmin`

**Agent permissions needed:**

- `modelarmor.templates.useToSanitizeUserPrompt`
- `modelarmor.templates.useToSanitizeModelResponse`

**Key CLI commands:**

```bash
# Create a Model Armor template
gcloud model-armor templates create TEMPLATE_ID \
  --location=LOCATION \
  --rai-settings-filters='[{"confidenceLevel":"MEDIUM_AND_ABOVE","filterType":"SEXUALLY_EXPLICIT"}]'

# Sanitize a user prompt
gcloud model-armor templates sanitize-user-prompt TEMPLATE_ID \
  --location=LOCATION \
  --user-prompt-data='{"text":"prompt text here"}'
```

Source: Model Armor · [Model Armor IAM](https://cloud.google.com/iam/docs/roles-permissions/modelarmor)

---

## Network Security

- VPC Service Controls enabled for Agent Engine
- Private IP addressing configured
- Firewall rules follow allowlist approach
- TLS 1.3 enforced for all connections

### Validation Commands

```bash
# Check VPC-SC perimeters
gcloud access-context-manager perimeters list \
  --policy=POLICY_ID --format="table(name, status.resources)"

# Verify restricted services
gcloud access-context-manager perimeters describe PERIMETER_NAME \
  --policy=POLICY_ID --format="yaml(status.restrictedServices)"
```

Source: [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs)

---

## Data Protection

- Encryption at rest with CMEK keys (preferred) or Google-managed
- Encryption in transit (TLS)
- Sensitive data handling complies with policies
- Secret Manager for API keys (`roles/secretmanager.secretAccessor`)

---

## Discovery Engine IAM (If Agents Use Search)

| Role | Access |
|------|--------|
| `roles/discoveryengine.admin` | Full access |
| `roles/discoveryengine.editor` | Create/update datastores, chat engines |
| `roles/discoveryengine.viewer` | Read-only |

Source: [Discovery Engine IAM](https://cloud.google.com/iam/docs/roles-permissions/discoveryengine)

---

## Identity Model Comparison

| Aspect | Agent Identity (2025+) | Custom Service Account | Default SA (Legacy) |
|--------|----------------------|------------------------|-------------------|
| Isolation | Per-agent | Shared | Shared |
| Lifecycle | Auto-cleanup | Manual | Manual |
| Security | CAA + mTLS | Manual mTLS | No mTLS |
| Credential theft | Un-replayable | Can be misused | Can be misused |
| Recommended | **Yes** | If legacy required | **No** |

Source: [Agent Engine Access Management](https://cloud.google.com/agent-builder/agent-engine/manage/access)
