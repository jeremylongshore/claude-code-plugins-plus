# External Reference Links Index

**Created:** November 13, 2025
**Purpose:** Comprehensive index of all external documentation, tutorials, and API references used across jeremy-firebase user manuals

---

## Manual 001: Vertex AI Agent Engine A2A Protocol Tutorial

**Source Notebook:** `agents/agent_engine/tutorial_a2a_on_agent_engine.ipynb`

### Primary Reference
- **GitHub Repository:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_a2a_on_agent_engine.ipynb

### Related Documentation
- Agent Engine Overview (referenced but URL not fully specified in manual)
- A2A Protocol Specification (referenced but URL not fully specified in manual)

---

## Manual 002: ADK Sessions and Memory Bank for Cloud Run

**Source Notebook:** `agents/cloud_run/agents_with_memory/get_started_with_memory_for_adk_in_cloud_run.ipynb`

### Primary Reference
- **GitHub Repository:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/cloud_run/agents_with_memory/get_started_with_memory_for_adk_in_cloud_run.ipynb

### Official Documentation
- **Agent Development Kit Documentation:** https://google.github.io/adk-docs/
- **Vertex AI Agent Engine Memory Bank:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview
- **Vertex AI Agent Engine Sessions:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview
- **Cloud Run Documentation:** https://cloud.google.com/run/docs/overview/what-is-cloud-run
- **Host AI apps and agents on Cloud Run:** https://cloud.google.com/run/docs/ai-agents
- **Deploying ADK agents to Cloud Run:** https://google.github.io/adk-docs/deploy/cloud-run/
- **ADK REST API endpoint:** https://google.github.io/adk-docs/get-started/testing/#api-endpoints (partially extracted)

### Console Links
- **Agent Memories Console:** https://console.cloud.google.com/vertex-ai/agents/locations/{LOCATION}/agent-engines/{agent_engine_id}/memories?project={PROJECT_ID}

---

## Manual 003: Agent Engine Terraform Deployment

**Source Notebook:** `agents/agent_engine/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb`

### Primary Reference
- **GitHub Repository:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb

### Official Documentation
- **Vertex AI Reasoning Engine Terraform Resource:** https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_reasoning_engine
- **Vertex AI Agent Engine Documentation:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **Agent Development Kit (ADK) Documentation:** https://google.github.io/adk-docs/
- **ADK Supported Operations:** https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/use/adk#supported-operations
- **Terraform Official Documentation:** https://www.terraform.io/docs (partially extracted)
- **Terraform Downloads:** https://www.terraform.io/downloads (partially extracted)

### External APIs
- **Frankfurter API (Currency Exchange):** https://api.frankfurter.app/
- **Frankfurter API Date Query:** https://api.frankfurter.app/{currency_date}

---

## Manual 004: Gemini Supervised Fine-Tuning for Predictive Maintenance

**Source Notebook:** `gemini/tuning/sft_gemini_predictive_maintenance.ipynb`

### Primary Reference
- **GitHub Repository:** https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/tuning/sft_gemini_predictive_maintenance.ipynb

### Official Documentation
- **Vertex AI Gemini Fine-tuning:** https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-tuning
- **Google GenAI SDK Documentation:** https://googleapis.github.io/python-genai/ (partially extracted)
- **Supervised Fine-Tuning Guide:** https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning (referenced but not fully extracted)
- **JSONL Format Requirements:** https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-tuning-format (referenced but not fully extracted)

---

## Summary by Documentation Category

### Google Cloud Platform Services
- **Vertex AI Agent Engine:** 6 references across manuals 001-003
- **Cloud Run:** 3 references in manual 002
- **Vertex AI Gemini:** 2 references in manual 004

### Developer Tools & SDKs
- **Agent Development Kit (ADK):** 5 references across manuals 002-003
- **Terraform:** 3 references in manual 003
- **Google GenAI SDK:** 1 reference in manual 004

### GitHub Repositories
- **GoogleCloudPlatform/generative-ai:** 4 primary source notebooks

### External APIs
- **Frankfurter Currency Exchange API:** 2 references in manual 003

---

## Next Steps

1. **Fetch Full Documentation:** Download complete versions of all referenced documentation
2. **Create Supplemental Guides:** Extract key sections relevant to jeremy-* plugins
3. **Build Cross-Reference Map:** Link each manual to relevant jeremy-* plugins
4. **Generate Quick Reference Cards:** Create one-page summaries of critical APIs/concepts

---

**Status:** Completed
**Total References Extracted:** 25+ unique documentation sources
**Coverage:** All 4 user manuals indexed
