# PRD: GCP Examples Expert

**Version:** 2.1.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Google Cloud's AI ecosystem spans six major frameworks (ADK, Agent Starter Pack, Genkit, Vertex AI, Generative AI, AgentSmithy), each with its own repository, patterns, and deployment targets. Developers waste hours searching through scattered repos to find the right starting code for their use case, then spend more time adapting examples that lack security, monitoring, and production deployment configuration. The gap between "hello world" examples and production-ready code causes teams to ship insecure or unmonitored AI applications.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| AI Engineer | Starting a new GCP AI project and unsure which framework to use | Framework selection guidance with a production-ready code example |
| Backend Developer | Implementing a specific pattern (RAG, agent, multimodal) on GCP | Working code adapted from the correct official repository with deployment config |
| Solutions Architect | Evaluating GCP AI services for an enterprise deployment | Comprehensive example with security (IAM, VPC-SC), monitoring, and cost estimates |
| DevOps Engineer | Setting up deployment pipelines for GCP AI applications | Terraform/IaC templates with deployment configuration for Cloud Run or Agent Engine |

## Success Criteria

1. Map any GCP AI request to the correct source repository and code pattern within the first response
2. Generated examples include IAM least-privilege, Secret Manager for credentials, and monitoring instrumentation
3. Every example includes a deployment configuration for at least one target (Cloud Run, Firebase Functions, or Agent Engine)
4. Source repository and official documentation links are cited for every pattern used
5. Generated code uses currently available Gemini models (2.5 Flash/Pro), not deprecated versions
6. Environment variable template provided listing all required secrets and API keys

## Functional Requirements

1. Identify the target framework by matching the request to one of six categories: ADK agents, Agent Starter Pack, Genkit flows, Vertex AI training, Generative AI multimodal, or AgentSmithy orchestration
2. Select the appropriate source repository and code pattern from the categorized reference
3. Adapt the template to the specified programming language (TypeScript, Python, or Go)
4. Configure security: IAM least-privilege service accounts, VPC Service Controls, Model Armor
5. Add monitoring: Cloud Monitoring dashboards, alerting policies, structured logging, OpenTelemetry
6. Set auto-scaling parameters with min/max instance counts for the deployment target
7. Include cost optimization: model selection rationale, token estimates, caching strategy
8. Generate deployment configuration for the target platform
9. Provide Terraform or IaC templates for reproducible infrastructure provisioning
10. Cite the source repository and link to official documentation

## Non-Functional Requirements

- All generated code must be runnable without modification (given correct credentials and project setup)
- API keys and credentials must use Secret Manager references, never inline values
- Examples must target currently available Gemini models (2.5 Flash/Pro), not deprecated versions
- Code must follow the style conventions of the source repository it's adapted from

## Dependencies

- Google Cloud project with billing enabled and Vertex AI API activated
- `gcloud` CLI authenticated with appropriate IAM roles
- Node.js 18+ for Genkit/TypeScript examples or Python 3.10+ for ADK/Vertex AI examples
- Firebase CLI for Genkit deployments
- API keys or service account credentials configured via Secret Manager

## Out of Scope

- Running or executing the generated code (the skill produces code, not executions)
- Non-Google Cloud platforms (AWS SageMaker, Azure AI)
- Custom model training or fine-tuning workflows
- Frontend or UI development for AI applications
- Ongoing maintenance or version updates of generated examples
- Proprietary or non-open-source GCP patterns
